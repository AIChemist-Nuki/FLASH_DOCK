import streamlit as st
import pandas as pd
from streamlit_molstar import st_molstar, st_molstar_rcsb, st_molstar_remote
# 如需使用口袋预测相关函数
from streamlit_molstar.pocket import (
    select_pocket_from_local_protein,
    # 如果你的项目需要也可以 import select_pocket_from_upload_protein
)
# docking 模块
from streamlit_molstar.docking import st_molstar_docking

import os
import json
import subprocess
import tempfile  # 用于创建临时文件
import re
import tqdm

import os
from rdkit import Chem
from rdkit.Chem import AllChem, Draw
import py3Dmol
from stmol import showmol
from streamlit_ketcher import st_ketcher
import zipfile


# ---- i18n 国际化 / Internationalization ----
@st.cache_data
def load_lang(lang_code):
    with open(f"./lang/{lang_code}.json", "r", encoding="utf-8") as f:
        return json.load(f)

LANGUAGES = {"中文": "zh", "English": "en", "日本語": "ja"}

# Language selector MUST be first sidebar element
selected_lang = st.sidebar.selectbox("🌐 Language", list(LANGUAGES.keys()), key="lang_selector")
lang_code = LANGUAGES[selected_lang]
_T = load_lang(lang_code)

def t(key, **kwargs):
    """Get translated string. Supports {placeholder} formatting."""
    text = _T.get(key, key)  # fallback to key if not found
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text

# Page keys (internal, never displayed)
PAGES = ["home", "prepare_ligand", "pocket_prediction", "docking", "batch_docking", "affinity_prediction", "task_manager", "author"]
PAGE_NAV_KEYS = {
    "home": "nav.home",
    "prepare_ligand": "nav.prepare_ligand",
    "pocket_prediction": "nav.pocket_prediction",
    "docking": "nav.docking",
    "batch_docking": "nav.batch_docking",
    "affinity_prediction": "nav.affinity_prediction",
    "task_manager": "nav.task_manager",
    "author": "nav.author",
}

if 'page' not in st.session_state:
    st.session_state['page'] = 'home'

st.sidebar.title(t("nav.title"))
for page_key in PAGES:
    if st.sidebar.button(t(PAGE_NAV_KEYS[page_key])):
        st.session_state['page'] = page_key

page = st.session_state['page']

# ------------------------------------------------------------------------------
# 主页
# ------------------------------------------------------------------------------
if page == "home":
    # 使用 HTML 和 Markdown 居中标题
    st.markdown(
        f"<h1 style='text-align: center;'>{t('home.welcome')}</h1>",
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # 显示图片 flashdock.png
    if os.path.exists("./others/flashdock.png"):
        st.image("./others/flashdock.png", use_container_width=True)
    else:
        st.error(t("home.error_flashdock_image"))

    # 在图片和其他内容之间插入若干空行
    st.markdown("<br><br><br><br><br>", unsafe_allow_html=True)

    # 显示 logo.png
    if os.path.exists("./others/logo.png"):
        st.image("./others/logo.png", use_container_width=True)
    else:
        st.error(t("home.error_logo_image"))

    st.markdown("<br><br><br><br><br><br><br><br>", unsafe_allow_html=True)
    # 在页面底部添加算法信息
    st.markdown("---")  # 分割线
    st.markdown(t("home.algorithms_title"))
    st.markdown(t("home.algorithms_list"))
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    # 下载按钮
    if os.path.exists("./examples/examples.zip"):
        with open("./examples/examples.zip", "rb") as file:
            st.download_button(
                label=t("home.download_examples"),
                data=file,
                file_name="examples.zip",
                mime="application/zip"
            )
    else:
        st.error(t("home.error_examples_zip"))
# ------------------------------------------------------------------------------
# 准备配体
# ------------------------------------------------------------------------------


elif page == "prepare_ligand":
    st.title(t("ligand.title"))

    # 使用选项卡分隔单个处理和批量处理
    tab1, tab2 = st.tabs([t("ligand.tab_single"), t("ligand.tab_batch")])

    with tab1:
        st.info(t("ligand.info_upload"))
        st.markdown(t("ligand.upload_label"))
        sdf_file = st.file_uploader(t("ligand.uploader_sdf"), type=["sdf"], key="single_sdf")

        st.markdown(t("ligand.draw_or_paste"))
        smiles_input = st_ketcher(key="single_ketcher")

        def process_and_show_mol(
            mol: Chem.Mol, 
            uploaded_sdf_name: str = None, 
            user_defined_filename: str = None
        ):
            """处理并展示单个分子"""
            if not mol:
                return

            try:
                # 处理手性
                Chem.AssignStereochemistry(mol, cleanIt=True, force=True)
                
                # 2D 可视化
                st.subheader(t("ligand.structure_2d"))
                img = Draw.MolToImage(mol, size=(300, 300))
                st.image(img, use_container_width=False)

                # 生成3D结构
                mol_3d = Chem.AddHs(mol)
                params = AllChem.ETKDGv3()
                params.randomSeed = 42

                # 检测手性中心
                chiral_centers = Chem.FindMolChiralCenters(mol_3d)
                params.enforceChirality = bool(chiral_centers)

                # 构象生成与优化
                embed_result = AllChem.EmbedMolecule(mol_3d, params)
                if embed_result == -1:
                    raise ValueError("构象生成失败")
                AllChem.MMFFOptimizeMolecule(mol_3d)

                # 3D 可视化
                st.subheader(t("ligand.structure_3d"))
                mol_block = Chem.MolToMolBlock(mol_3d)
                xyzview = py3Dmol.view(width=500, height=400)
                xyzview.addModel(mol_block, "mol")
                xyzview.setStyle({'stick': {}})
                xyzview.zoomTo()
                showmol(xyzview, height=400, width=500)

                # 生成下载文件
                if uploaded_sdf_name:
                    base_name = os.path.splitext(uploaded_sdf_name)[0]
                    out_filename = f"{base_name}_prepared.sdf"
                else:
                    clean_name = re.sub(r'[^a-zA-Z0-9_]', '', user_defined_filename.strip())
                    out_filename = f"{clean_name}.sdf" if user_defined_filename else "ligand_3d.sdf"

                st.download_button(
                    label=t("ligand.download_mol"),
                    data=mol_block,
                    file_name=out_filename,
                    mime="chemical/x-mdl-sdfile",
                    use_container_width=True
                )

            except Exception as e:
                st.error(t("ligand.error_processing", error=str(e)))

        # 单个分子处理逻辑
        if sdf_file is not None:
            try:
                with st.spinner(t("ligand.spinner_parse_sdf")):
                    suppl = Chem.ForwardSDMolSupplier(sdf_file)
                    mol = next((m for m in suppl if m is not None), None)
                    if mol:
                        process_and_show_mol(mol, sdf_file.name)
                    else:
                        st.error(t("ligand.error_no_molecule"))
            except Exception as e:
                st.error(t("ligand.error_sdf_parse", error=str(e)))
        elif smiles_input:
            with st.spinner(t("ligand.spinner_process_smiles")):
                mol = Chem.MolFromSmiles(smiles_input)
                if mol:
                    user_name = st.text_input(t("ligand.filename_label"), value=t("ligand.filename_default"))
                    process_and_show_mol(mol, user_defined_filename=user_name)
                else:
                    st.error(t("ligand.error_invalid_smiles"))

    with tab2:
        st.subheader(t("ligand.batch_title"))
        st.markdown("""
        **CSV文件格式要求：**
        - 必须包含 `mol_name` 和 `smiles` 两列
        - `mol_name` 将用作生成的文件名（仅允许字母、数字和下划线）
        - 示例格式：
        ```
        mol_name | smiles
        ethanol  | CCO
        caffeine | CN1C=NC2=C1C(=O)N(C(=O)N2C)C
        """
        )

        csv_file = st.file_uploader(t("ligand.batch_uploader"), type=["csv"], key="batch_csv")
        
        if csv_file:
            with st.spinner(t("ligand.spinner_batch_process")):
                try:
                    df = pd.read_csv(csv_file)
                    if not {'smiles', 'mol_name'}.issubset(df.columns):
                        st.error(t("ligand.error_batch_columns"))
                        st.stop()

                    # 创建临时工作区
                    with tempfile.TemporaryDirectory() as tmpdir:
                        zip_path = os.path.join(tmpdir, "processed_molecules.zip")
                        error_log = []
                        success_count = 0

                        progress_bar = st.progress(0)
                        total = len(df)
                        
                        with zipfile.ZipFile(zip_path, 'w') as zipf:
                            for idx, row in df.iterrows():
                                try:
                                    # 检查进度
                                    if idx % 1 == 0:
                                        progress = (idx + 1) / total
                                        progress_bar.progress(min(progress, 1.0))
                                    
                                    # 验证分子名称
                                    mol_name = re.sub(r'[^a-zA-Z0-9_]', '', str(row['mol_name']))
                                    if not mol_name:
                                        raise ValueError("无效的分子名称")

                                    # 解析SMILES
                                    mol = Chem.MolFromSmiles(row['smiles'])
                                    if not mol:
                                        raise ValueError("无效的SMILES格式")
                                    
                                    # 处理手性
                                    Chem.AssignStereochemistry(mol, cleanIt=True, force=True)
                                    chiral_centers = Chem.FindMolChiralCenters(mol)
                                    
                                    # 生成3D结构
                                    mol = Chem.AddHs(mol)
                                    params = AllChem.ETKDGv3()
                                    params.randomSeed = 42
                                    params.enforceChirality = bool(chiral_centers)
                                    
                                    embed_result = AllChem.EmbedMolecule(mol, params)
                                    if embed_result == -1:
                                        raise ValueError("构象生成失败")
                                    AllChem.MMFFOptimizeMolecule(mol)

                                    # 保存文件
                                    sdf_path = os.path.join(tmpdir, f"{mol_name}.sdf")
                                    with Chem.SDWriter(sdf_path) as writer:
                                        writer.write(mol)
                                    
                                    zipf.write(sdf_path, arcname=f"{mol_name}.sdf")
                                    success_count += 1
                                
                                except Exception as e:
                                    error_log.append(f"行 {idx+1}: {str(e)}")
                                    continue

                        # 处理完成
                        progress_bar.progress(1.0)
                        
                        # 显示处理结果
                        st.markdown(t("ligand.batch_complete", success_count=success_count, error_count=len(error_log)))

                        if error_log:
                            with st.expander(t("ligand.error_details"), expanded=False):
                                st.write("\n".join(error_log))

                        # 提供下载
                        with open(zip_path, "rb") as f:
                            st.download_button(
                                label=t("ligand.batch_download"),
                                data=f,
                                file_name="processed_molecules.zip",
                                mime="application/zip",
                                key="batch_download"
                            )

                except pd.errors.EmptyDataError:
                    st.error(t("ligand.error_empty_csv"))
                except pd.errors.ParserError:
                    st.error(t("ligand.error_csv_parse"))
                except Exception as e:
                    st.error(t("ligand.error_file_process", error=str(e)))


# ------------------------------------------------------------------------------
# 口袋预测
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# 口袋预测
# ------------------------------------------------------------------------------


elif page == "pocket_prediction":
    import streamlit as st
    import pandas as pd
    import tempfile
    import os
    import hashlib
    from pathlib import Path
    import sh

    TMP_ROOT = Path(tempfile.gettempdir()) / "streamlit-molstar"
    TMP_ROOT.mkdir(exist_ok=True)

    # Helper functions
    def _get_file_type(file_path):
        return os.path.splitext(file_path)[1][1:].lower()

    def get_workspace_info(md5hash, ftype, fresh=False, create=True):
        workdir_p = TMP_ROOT / md5hash
        if fresh and workdir_p.exists():
            sh.rm('-r', str(workdir_p))
        if create:
            workdir_p.mkdir(parents=True, exist_ok=True)
        protein_name = f'{md5hash}-protein.{ftype}'
        protein_file_path_p = workdir_p / protein_name
        pockets_file_path_p = workdir_p / f'{protein_name}_predictions.csv'
        return {
            "workdir": str(workdir_p),
            "protein_file_path": str(protein_file_path_p),
            "pockets_file_path": str(pockets_file_path_p),
        }

    def batch_predict_pockets(protein_file_paths, original_filenames, p2rank_home):
        all_pockets_data = []

        for protein_file_path, original_name in zip(protein_file_paths, original_filenames):
            with open(protein_file_path, 'rb') as f:
                content = f.read()
                md5hash = hashlib.md5(content).hexdigest()
            
            ftype = _get_file_type(protein_file_path)
            workspace_info = get_workspace_info(md5hash, ftype, fresh=True, create=True)

            # Copy protein file to workspace
            sh.cp(protein_file_path, workspace_info['protein_file_path'])

            # Run p2rank prediction
            predict_path_p = Path(workspace_info['workdir']) / 'predict'
            predict_path_p.mkdir(parents=True, exist_ok=True)
            cmd = sh.Command(os.path.join(p2rank_home, 'prank'))
            args = ['predict', '-f', workspace_info['protein_file_path'], '-o', str(predict_path_p)]
            cmd(*args, _cwd=p2rank_home, _fg=True)

            protein_file_name = os.path.basename(workspace_info['protein_file_path'])
            tmp_pockets_file_path_p = predict_path_p / f'{protein_file_name}_predictions.csv'
            sh.cp(str(tmp_pockets_file_path_p), workspace_info['pockets_file_path'])

            # Load predictions and use original filename
            df = pd.read_csv(workspace_info['pockets_file_path'])
            df['Protein File'] = original_name  # Use original filename here
            all_pockets_data.append(df)

        if all_pockets_data:
            result_df = pd.concat(all_pockets_data, ignore_index=True)
            return result_df
    st.title(t("pocket.title"))

    # 让用户选择如何加载蛋白质
    POCKET_OPTIONS = {
        "single": t("pocket.mode_single"),
        "batch": t("pocket.mode_batch"),
        "example": t("pocket.mode_example")
    }
    option = st.radio("Select how to load the protein:", list(POCKET_OPTIONS.values()))

    # 用于保存用户上传的蛋白文件名称（用于替换 Pocket Name）
    uploaded_pdb_filename = None

    if option == POCKET_OPTIONS["single"]:
        try:
            # 用户上传蛋白质（只出现一次，不会再弹二次上传）
            pdb_file = st.file_uploader(t("pocket.uploader_pdb"), type=["pdb"])
            
            if pdb_file is not None:
                # 记下上传的名称
                uploaded_pdb_filename = pdb_file.name

                # 使用临时文件的方式进行口袋预测
                with tempfile.NamedTemporaryFile(suffix=".pdb", delete=False) as tmp:
                    tmp.write(pdb_file.getvalue())
                    tmp.flush()
                    file_path = tmp.name

                # 调用 p2rank (或其他函数) ，读取该临时文件进行预测
                selected = select_pocket_from_local_protein(
                    file_path,
                    p2rank_home='./others/p2rank_2.5/'
                )
                # 预测完成后删除该临时文件
                os.remove(file_path)

                if selected:
                    pocket = selected
                    st.write(t("pocket.info_predicted"), pocket)

                    # 如果 rank=1 的口袋
                    if pocket['rank'] == '1':
                        # 如果上传了文件名，则用之，否则用 pocket['name']
                        final_name = uploaded_pdb_filename if uploaded_pdb_filename else pocket['name']
                        data = {
                            'Pocket Name': [final_name],
                            'Center': [pocket['center']],
                        }
                        df = pd.DataFrame(data)

                        st.write(t("pocket.preview_optimal"))
                        st.dataframe(df)

                        # 用户点击按钮后，才将CSV保存到指定文件夹
                        # 使用 Streamlit 的 download_button 提供单次点击的下载
                        csv_data = df.to_csv(index=False)  # 将 DataFrame 转换为 CSV 数据

                        # 直接显示一个下载按钮
                        st.download_button(
                            label=t("pocket.download_csv"),
                            data=csv_data,
                            file_name="best_pocket.csv",
                            mime="text/csv",
                            use_container_width=True
                        )

        except Exception as e:
            st.warning(t("pocket.error_upload", error=str(e)))

    elif option == POCKET_OPTIONS["example"]:
        try:
            # 用示例文件名
            uploaded_pdb_filename = "protein_example.pdb"
            # 调用 p2rank 做预测
            selected = select_pocket_from_local_protein(
                "examples/pocket/protein.pdb", 
                p2rank_home='./others/p2rank_2.5/'
            )
            if selected:
                pocket = selected
                st.write(t("pocket.info_predicted"), pocket)

                if pocket['rank'] == '1':
                    data = {
                        'Pocket Name': [uploaded_pdb_filename],
                        'Center': [pocket['center']],
                    }
                    df = pd.DataFrame(data)

                    st.write(t("pocket.preview_optimal"))
                    st.dataframe(df)

                    # 将 DataFrame 转换为 CSV 格式的字符串
                    csv_data = df.to_csv(index=False)

                    # 使用 Streamlit 的 download_button 提供单次点击的下载
                    st.download_button(
                        label=t("pocket.download_csv"),
                        data=csv_data,
                        file_name="best_pocket.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

        except Exception as e:
            st.warning(t("pocket.error_example", error=str(e)))

    elif option == POCKET_OPTIONS["batch"]:
        st.header(t("pocket.batch_title"))
        uploaded_files = st.file_uploader(t("pocket.batch_uploader"), type=["pdb"], accept_multiple_files=True)

        if uploaded_files:
            protein_file_paths = []
            original_filenames = []

            for file in uploaded_files:
                with tempfile.NamedTemporaryFile(suffix=".pdb", delete=False) as tmp:
                    tmp.write(file.getvalue())
                    tmp.flush()
                    protein_file_paths.append(tmp.name)
                    original_filenames.append(file.name)  # 存储原始文件名

            if st.button(t("pocket.batch_button")):
                progress_bar = st.progress(0)
                status_text = st.empty()

                results = []
                total_files = len(protein_file_paths)

                for i, (file_path, original_name) in enumerate(zip(protein_file_paths, original_filenames)):
                    status_text.text(t("pocket.batch_progress", name=original_name, current=i+1, total=total_files))
                    single_result = batch_predict_pockets([file_path], [original_name], p2rank_home='./others/p2rank_2.5/')
                    results.append(single_result)
                    progress_bar.progress((i + 1) / total_files)

                result_df = pd.concat(results, ignore_index=True)
                status_text.text(t("pocket.batch_success"))
                st.success(t("pocket.batch_success"))

                # 显示和下载结果
                st.dataframe(result_df)
                csv_data = result_df.to_csv(index=False)
                st.download_button(
                    label=t("pocket.batch_download"),
                    data=csv_data,
                    file_name="batch_pocket_predictions.csv",
                    mime="text/csv",
                    use_container_width=True
                )

            # 清理临时文件
            for path in protein_file_paths:
                if os.path.exists(path):
                    os.remove(path)

# ------------------------------------------------------------------------------
# 分子对接
# ------------------------------------------------------------------------------
elif page == "docking":



    st.title(t("dock.title"))
    st.write(t("dock.instruction"))

    # 上传蛋白质和配体文件
    protein_file = st.file_uploader(t("dock.uploader_protein"), type=["pdb"])
    ligand_file = st.file_uploader(t("dock.uploader_ligand"), type=["sdf"])

    # 上传口袋预测结果文件（可选）
    st.write(t("dock.info_pocket_csv"))
    pocket_csv_file = st.file_uploader(t("dock.uploader_pocket_csv"), type=["csv"])

    # 默认网格参数
    center_x = 0.0
    center_y = 0.0
    center_z = 0.0

    # 处理 CSV 文件获取网格参数
    if pocket_csv_file is not None:
        try:
            pocket_df = pd.read_csv(pocket_csv_file)
            if "Center" in pocket_df.columns:
                center_coords = pocket_df.loc[0, "Center"]
                if isinstance(center_coords, str):
                    coords = [float(c) for c in re.findall(r"[-+]?[0-9]*\.?[0-9]+", center_coords)]
                    if len(coords) == 3:
                        center_x, center_y, center_z = coords
                    else:
                        st.warning(t("dock.warning_csv_format"))
                else:
                    st.warning(t("dock.warning_csv_format"))
            else:
                st.warning(t("dock.warning_no_center"))
        except Exception as e:
            st.error(t("dock.error_csv_read", error=str(e)))

    # 网格参数输入框
    st.subheader(t("dock.parameters_title"))
    center_x = st.number_input("Center X", value=center_x)
    center_y = st.number_input("Center Y", value=center_y)
    center_z = st.number_input("Center Z", value=center_z)

    size_x = st.number_input("Size X", value=100.0)
    size_y = st.number_input("Size Y", value=100.0)
    size_z = st.number_input("Size Z", value=100.0)

    # 对接按钮
    if st.button(t("dock.button_start"), key="start_docking"):
        if not protein_file or not ligand_file:
            st.error(t("dock.error_missing_files"))
        else:
            try:
                # 创建临时文件夹保存缓存文件
                with tempfile.TemporaryDirectory() as temp_dir:
                    docking_grid = {
                        "center_x": center_x,
                        "center_y": center_y,
                        "center_z": center_z,
                        "size_x": size_x,
                        "size_y": size_y,
                        "size_z": size_z
                    }
                    docking_grid_path = os.path.join(temp_dir, "docking_grid.json")

                    # 保存网格参数为 JSON 文件
                    with open(docking_grid_path, "w") as f:
                        json.dump(docking_grid, f, indent=4)

                    # 保存蛋白质和配体文件到临时目录
                    protein_path = os.path.join(temp_dir, "protein.pdb")
                    ligand_path = os.path.join(temp_dir, "ligand.sdf")

                    with open(protein_path, "wb") as f:
                        f.write(protein_file.getvalue())

                    with open(ligand_path, "wb") as f:
                        f.write(ligand_file.getvalue())

                    # 构造对接命令
                    output_ligand_name = "ligand_predict"
                    command = (
                        f"python ./others/Uni-Mol/unimol_docking_v2/interface/demo.py "
                        f"--mode single "
                        f"--conf-size 10 "
                        f"--cluster "
                        f"--input-protein {protein_path} "
                        f"--input-ligand {ligand_path} "
                        f"--input-docking-grid {docking_grid_path} "
                        f"--output-ligand-name {output_ligand_name} "
                        f"--output-ligand-dir {temp_dir} "
                        f"--steric-clash-fix "
                        f"--model-dir ./others/Uni-Mol/unimol_docking_v2/unimol_docking_v2_240517.pt"
                    )

                    # 执行命令
                    result = subprocess.run(command, shell=True, capture_output=True, text=True)

                    # 判断是否成功
                    if result.returncode == 0:
                        st.success(t("dock.success_complete"))
                        st.text_area("Docking Output Log", value=result.stdout, height=150)

                        # 处理对接结果文件
                        try:
                            ligand_output_path = os.path.join(temp_dir, f"{output_ligand_name}.sdf")

                            # 重命名输出文件
                            output_name = f"{os.path.splitext(protein_file.name)[0]}_{os.path.splitext(ligand_file.name)[0]}__docked.sdf"
                            renamed_path = os.path.join(temp_dir, output_name)
                            os.rename(ligand_output_path, renamed_path)

                            # 提供下载按钮
                            with open(renamed_path, "rb") as f:
                                sdf_data = f.read()
                                st.download_button(
                                    label=t("dock.download_result"),
                                    data=sdf_data,
                                    file_name=output_name,
                                    mime="chemical/x-mdl-sdfile",
                                    use_container_width=True
                                )

                            # 可视化对接结果
                            st_molstar_docking(
                                protein_path,
                                renamed_path,
                                key="5",
                                height=600
                            )
                        except Exception as e:
                            st.error(t("dock.error_result_file"))
                    else:
                        st.error(t("dock.error_failed"))
                        st.text_area("Error Message", value=result.stderr, height=150)

            except Exception as e:
                st.error(t("dock.error_process", error=str(e)))


# ------------------------------------------------------------------------------
# 批量口袋预测与对接
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# 批量口袋预测与对接
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# 批量口袋预测与对接
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# 批量口袋预测与对接
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# 批量口袋预测与对接
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# 批量口袋预测与对接
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# 批量口袋预测与对接
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# 批量分子对接（基于已有口袋预测结果）
# ------------------------------------------------------------------------------
elif page == "batch_docking":
    import os
    import uuid
    import time
    import pandas as pd
    import subprocess
    import json
    import zipfile
    from pathlib import Path
    import streamlit as st
    import shutil
    from threading import Thread

    # 初始化任务存储目录
    JOBS_DIR = Path("./jobs")
    JOBS_DIR.mkdir(exist_ok=True)

    # 任务管理函数
    def init_job(job_id):
        """初始化任务目录结构"""
        job_dir = JOBS_DIR / job_id
        (job_dir / "uploads").mkdir(parents=True, exist_ok=True)
        (job_dir / "results").mkdir(exist_ok=True)
        return job_dir

    def save_job_status(job_id, status):
        """保存任务状态"""
        status_file = JOBS_DIR / job_id / "status.json"
        with open(status_file, "w") as f:
            json.dump(status, f)

    def get_job_status(job_id):
        """获取任务状态"""
        status_file = JOBS_DIR / job_id / "status.json"
        try:
            with open(status_file) as f:
                return json.load(f)
        except:
            return {"state": "not_found", "progress": 0, "log": []}

    # 对接处理线程
    def process_docking_tasks(job_id, tasks_to_run, pockets_df):
        job_dir = JOBS_DIR / job_id
        status = {
            "state": "running",
            "progress": 0,
            "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "log": []
        }
        
        try:
            save_job_status(job_id, status)
            
            # 准备zip文件
            zip_path = job_dir / "results" / "docking_results.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                
                total_tasks = len(tasks_to_run)
                for i, task in enumerate(tasks_to_run.iterrows()):
                    idx = i + 1
                    _, row = task
                    protein_path = job_dir / "uploads" / row["Protein"]
                    ligand_path = job_dir / "uploads" / row["Ligand"]
                    
                    # 更新状态
                    status["log"].append(f"任务 {idx}/{total_tasks}: 对接 {row['Protein']} 和 {row['Ligand']}")
                    status["progress"] = idx / total_tasks
                    save_job_status(job_id, status)
                    
                    # 从CSV中获取口袋中心坐标
                    try:
                        # 标准化列名（不区分大小写）
                        protein_col = next(col for col in pockets_df.columns if col.lower() == "protein file")
                        rank_col = next(col for col in pockets_df.columns if col.lower() == "rank")
                        center_x_col = next(col for col in pockets_df.columns if col.lower() == "center_x")
                        center_y_col = next(col for col in pockets_df.columns if col.lower() == "center_y")
                        center_z_col = next(col for col in pockets_df.columns if col.lower() == "center_z")
                        
                        # 获取当前蛋白的rank1口袋
                        protein_filename = row["Protein"]
                        protein_pockets = pockets_df[pockets_df[protein_col] == protein_filename]
                        
                        if len(protein_pockets) == 0:
                            status["log"].append(f"任务 {idx} 错误: 蛋白 {protein_filename} 无口袋数据")
                            continue
                            
                        # 获取rank1口袋
                        rank1_pocket = protein_pockets[protein_pockets[rank_col] == 1].iloc[0]
                        center_coords = [
                            float(rank1_pocket[center_x_col]),
                            float(rank1_pocket[center_y_col]),
                            float(rank1_pocket[center_z_col])
                        ]
                        status["log"].append(f"任务 {idx} 使用口袋中心坐标: {center_coords}")
                        
                    except Exception as e:
                        status["log"].append(f"任务 {idx} 获取口袋坐标失败: {str(e)}")
                        continue

                    # 生成对接网格
                    docking_grid = {
                        "center_x": center_coords[0],
                        "center_y": center_coords[1],
                        "center_z": center_coords[2],
                        "size_x": 25.0,
                        "size_y": 25.0,
                        "size_z": 25.0,
                    }
                    grid_path = job_dir / f"grid_{idx}.json"
                    with open(grid_path, "w") as f:
                        json.dump(docking_grid, f)
                    
                    # 执行对接命令
                    output_ligand_name = f"{Path(ligand_path).stem}_predict"
                    command = (
                        f"python ./others/Uni-Mol/unimol_docking_v2/interface/demo.py "
                        f"--mode single "
                        f"--conf-size 10 "
                        f"--cluster "
                        f"--input-protein {protein_path} "
                        f"--input-ligand {ligand_path} "
                        f"--input-docking-grid {grid_path} "
                        f"--output-ligand-name {output_ligand_name} "
                        f"--output-ligand-dir {job_dir / 'results'} "
                        f"--steric-clash-fix "
                        f"--model-dir ./others/Uni-Mol/unimol_docking_v2/unimol_docking_v2_240517.pt"
                    )
                    
                    result = subprocess.run(command, shell=True, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        # 保存结果到zip
                        output_path = job_dir / "results" / f"{output_ligand_name}.sdf"
                        zip_name = f"{Path(protein_path).stem}_{Path(ligand_path).stem}_docked.sdf"
                        zipf.write(output_path, zip_name)
                        status["log"].append(f"任务 {idx} 对接成功")
                    else:
                        status["log"].append(f"对接失败: {result.stderr}")
                    
                    # 清理临时文件
                    if grid_path.exists():
                        grid_path.unlink()
            
            # 最终状态
            status["state"] = "completed"
            status["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
            save_job_status(job_id, status)
            
        except Exception as e:
            status["state"] = "failed"
            status["log"].append(f"处理失败: {str(e)}")
            save_job_status(job_id, status)

    # 页面布局
    st.title(t("batch.title"))

    # 任务查询模块
    st.subheader(t("batch.query_title"))
    job_id = st.text_input(t("batch.job_id_input"))
    if job_id:
        status = get_job_status(job_id)
        if status["state"] == "not_found":
            st.error(t("batch.error_job_not_found"))
        else:
            st.write(t("batch.job_status", status=status['state'].upper()))
            st.download_button(
                t("batch.download_job_result"),
                data=(JOBS_DIR / job_id / "results" / "docking_results.zip").read_bytes(),
                file_name=f"results_{job_id}.zip",
                disabled=status["state"] != "completed"
            )

            # ---- 可视化对接结果 ----
            if status["state"] == "completed":
                st.subheader(t("batch.visualization_title"))
                job_dir_q = JOBS_DIR / job_id
                zip_path_q = job_dir_q / "results" / "docking_results.zip"

                with zipfile.ZipFile(zip_path_q, 'r') as zf:
                    docked_sdfs = [n for n in zf.namelist() if n.endswith("_docked.sdf")]

                if docked_sdfs:
                    selected_sdf = st.selectbox(t("batch.select_result"), docked_sdfs, key="batch_vis_select")

                    if st.button(t("batch.view_3d"), key="batch_vis_btn"):
                        # 在 uploads 中匹配对应的蛋白 PDB
                        pdb_match = None
                        for pdb_f in sorted((job_dir_q / "uploads").glob("*.pdb"), key=lambda p: len(p.stem), reverse=True):
                            if selected_sdf.startswith(pdb_f.stem + "_"):
                                pdb_match = pdb_f
                                break

                        if pdb_match:
                            # 从 ZIP 解压选中的 SDF（因为 results/ 目录中同名配体会互相覆盖）
                            vis_dir = job_dir_q / "vis_tmp"
                            vis_dir.mkdir(exist_ok=True)
                            with zipfile.ZipFile(zip_path_q, 'r') as zf:
                                (vis_dir / selected_sdf).write_bytes(zf.read(selected_sdf))

                            st_molstar_docking(
                                str(pdb_match),
                                str(vis_dir / selected_sdf),
                                key=f"vis_{selected_sdf}",
                                height=600
                            )
                        else:
                            st.error(t("batch.error_no_pdb"))
                else:
                    st.info(t("batch.info_no_results"))

            st.subheader(t("batch.job_log"))
            st.write("\n".join(status["log"]))

    # 新任务提交模块
    st.subheader(t("batch.new_task_title"))

    # 上传口袋预测结果CSV
    pockets_csv = st.file_uploader(
        t("batch.uploader_pocket"),
        type=["csv"],
        help=t("batch.help_pocket_csv")
    )
    
    if pockets_csv:
        try:
            pockets_df = pd.read_csv(pockets_csv)
            # 标准化列名（不区分大小写）
            pockets_df.columns = [col.strip().lower() for col in pockets_df.columns]
            st.success(t("batch.success_pocket_loaded", count=len(pockets_df)))

            # 显示口袋数据预览
            with st.expander(t("batch.view_pocket_data")):
                st.dataframe(pockets_df)

            # 上传蛋白质和配体文件
            uploaded_files = st.file_uploader(
                t("batch.uploader_ligands"),
                type=["pdb", "sdf"],
                accept_multiple_files=True,
                key="mol_files"
            )
            
            if uploaded_files:
                # 生成任务ID
                job_id = str(uuid.uuid4())[:8]
                job_dir = init_job(job_id)
                
                # 保存上传文件
                upload_dir = job_dir / "uploads"
                for f in uploaded_files:
                    (upload_dir / f.name).write_bytes(f.getbuffer())
                
                # 生成任务CSV
                pdb_files = [f.name for f in upload_dir.glob("*.pdb")]
                sdf_files = [f.name for f in upload_dir.glob("*.sdf")]
                tasks = []
                for p in pdb_files:
                    for s in sdf_files:
                        tasks.append({"Protein": p, "Ligand": s, "Run": "Yes"})
                task_df = pd.DataFrame(tasks)
                task_csv = task_df.to_csv(index=False)
                (job_dir / "tasks.csv").write_text(task_csv)
                
                # 显示任务信息
                st.success(t("batch.success_task_created", job_id=job_id))
                st.download_button(
                    t("batch.download_task_csv"),
                    data=task_csv,
                    file_name="tasks.csv",
                    help=t("batch.help_edit_csv")
                )


                # 上传修改后的CSV
                modified_csv = st.file_uploader(t("batch.uploader_modified_csv"), type=["csv"])
                if modified_csv:
                    # 保存修改后的任务文件
                    (job_dir / "modified_tasks.csv").write_bytes(modified_csv.getvalue())
                    st.success(t("batch.success_task_updated"))

                    # 解析任务
                    try:
                        tasks_df = pd.read_csv(job_dir / "modified_tasks.csv")
                        tasks_to_run = tasks_df[tasks_df["Run"].str.lower() == "yes"]
                        st.write(t("batch.prepare_run", count=len(tasks_to_run)))

                        # 添加任务数量检查提示
                        if len(tasks_to_run) > 200:
                            st.warning(t("batch.warning_task_limit"))

                        if st.button(t("batch.button_start")):
                            # 添加正式的任务数量检查
                            if len(tasks_to_run) > 200:
                                st.error(t("batch.error_task_limit", count=len(tasks_to_run)))
                            else:
                                # 启动处理线程
                                Thread(target=process_docking_tasks, args=(job_id, tasks_to_run, pockets_df)).start()
                                st.success(t("batch.success_started", job_id=job_id))


                    except Exception as e:
                        st.error(t("batch.error_csv_parse", error=str(e)))

        except Exception as e:
            st.error(t("batch.error_pocket_parse", error=str(e)))

    # 样式调整
    st.markdown("""
    <style>
    .stDownloadButton > button {
        width: 100%;
        justify-content: center;
    }
    </style>
    """, unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# 预测亲和力
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# 预测亲和力
# ------------------------------------------------------------------------------
# 在原代码的"预测亲和力"部分替换为以下代码
# 在原代码的"预测亲和力"部分替换为以下代码

elif page == "affinity_prediction":
    import os
    import tempfile
    import subprocess
    import pandas as pd
    import streamlit as st
    import matplotlib.pyplot as plt
    import seaborn as sns
    import numpy as np
    from pathlib import Path
    import io

    # 初始化 session_state
    if 'affinity_results_df' not in st.session_state:
        st.session_state.affinity_results_df = None
    if 'prediction_completed' not in st.session_state:
        st.session_state.prediction_completed = False

    st.title(t("affinity.title"))
    st.write(t("affinity.instruction"))

    # 创建选项卡
    tab1, tab2, tab3 = st.tabs([t("affinity.tab_single"), t("affinity.tab_data"), t("affinity.tab_heatmap")])

    with tab1:
        st.subheader(t("affinity.subtitle_predict"))

        # 模式选择
        mode = st.radio(t("affinity.mode_label"), (t("affinity.mode_single"), t("affinity.mode_batch")))

        if mode == t("affinity.mode_single"):
            st.subheader(t("affinity.single_title"))

            # 用户上传蛋白质 PDB 文件
            protein_file = st.file_uploader(t("affinity.uploader_protein"), type=["pdb"])

            # 用户上传小分子 SDF 文件
            ligand_file = st.file_uploader(t("affinity.uploader_ligand"), type=["sdf"])

            # 按钮触发预测
            if st.button(t("affinity.button_predict"), key="start_single_predicting"):
                if protein_file is None:
                    st.error(t("affinity.error_no_protein"))
                elif ligand_file is None:
                    st.error(t("affinity.error_no_ligand"))
                else:
                    with st.spinner(t("affinity.spinner_predicting")):
                        try:
                            # 创建临时目录
                            with tempfile.TemporaryDirectory() as tmpdir:
                                # 保存上传的蛋白质文件
                                protein_path = os.path.join(tmpdir, protein_file.name)
                                with open(protein_path, "wb") as f:
                                    f.write(protein_file.getbuffer())

                                # 保存上传的小分子文件
                                ligand_path = os.path.join(tmpdir, ligand_file.name)
                                with open(ligand_path, "wb") as f:
                                    f.write(ligand_file.getbuffer())

                                # 输出 CSV 文件路径
                                output_csv_path = os.path.join(tmpdir, "single_prediction.csv")

                                # 调用预测脚本
                                pred_dir = "./others/PLANET"
                                pred_script = "pred.py"
                                pred_script_path = os.path.join(pred_dir, pred_script)

                                cmd = [
                                    "python",
                                    pred_script_path,
                                    "-p", protein_path,
                                    "-l", ligand_path,
                                    "-m", ligand_path,
                                    "-o", output_csv_path
                                ]

                                result = subprocess.run(cmd, capture_output=True, text=True)

                                if result.returncode != 0:
                                    st.error(f"Error during prediction:\n{result.stderr}")
                                else:
                                    if os.path.exists(output_csv_path):
                                        df = pd.read_csv(output_csv_path)
                                        st.success(t("affinity.success_complete"))
                                        st.dataframe(df)

                                        # 保存到session state
                                        st.session_state.affinity_results_df = df
                                        st.session_state.prediction_completed = True

                                        # 提供下载
                                        csv_data = df.to_csv(index=False)
                                        st.download_button(
                                            label=t("affinity.download_result"),
                                            data=csv_data,
                                            file_name="single_prediction_result.csv",
                                            mime="text/csv"
                                        )
                                    else:
                                        st.error(t("affinity.error_no_output"))
                        except Exception as e:
                            st.error(t("affinity.error_exception", error=str(e)))

        elif mode == t("affinity.mode_batch"):
            st.subheader(t("affinity.batch_title"))

            # 用户上传多个文件（PDB 和 SDF 格式）
            uploaded_files = st.file_uploader(
                t("affinity.batch_uploader"),
                type=["pdb", "sdf"],
                accept_multiple_files=True
            )

            if uploaded_files:
                # 创建临时目录并保存上传的文件
                with tempfile.TemporaryDirectory() as temp_dir:
                    batch_docking_dir = Path(temp_dir)
                    os.makedirs(batch_docking_dir, exist_ok=True)

                    # 保存上传的文件到临时文件夹
                    for uploaded_file in uploaded_files:
                        file_path = batch_docking_dir / uploaded_file.name
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                    # 显示已上传的文件
                    st.write(t("affinity.uploaded_files"))
                    st.write([file.name for file in batch_docking_dir.iterdir()])

                    # 扫描文件夹中的 SDF 和 PDB 文件
                    sdf_files = [file.name for file in batch_docking_dir.glob("*.sdf")]
                    pdb_files = [file.name for file in batch_docking_dir.glob("*.pdb")]

                    if not pdb_files:
                        st.error(t("affinity.error_no_pdb"))
                    elif not sdf_files:
                        st.error(t("affinity.error_no_sdf"))
                    else:
                        # 自动生成任务列表
                        tasks = []
                        for sdf_file in sdf_files:
                            try:
                                # 使用 split("_", 1) 分割文件名
                                parts = sdf_file.split("_", 1)
                                if len(parts) < 2:
                                    raise ValueError("文件名缺少下划线分隔符")
                                    
                                receptor_name = parts[0]
                                ligand_part = parts[1]
                                
                                # 清理后缀和扩展名
                                ligand_name = ligand_part.replace("_docked", "").split(".", 1)[0]
                                pdb_file = f"{receptor_name}.pdb"
                                
                                tasks.append({
                                    "Protein": pdb_file,
                                    "Ligand": sdf_file,
                                    "Run": "Yes"
                                })
                            except Exception as e:
                                st.warning(t("affinity.warning_file_format", filename=sdf_file, error=str(e)))

                        if not tasks:
                            st.error(t("affinity.error_no_tasks"))
                        else:
                            # 显示自动生成的任务列表
                            st.subheader(t("affinity.auto_matched_tasks"))
                            st.dataframe(pd.DataFrame(tasks))

                            if st.button(t("affinity.button_batch_predict"), key="start_batch_predicting"):
                                with st.spinner(t("affinity.spinner_batch_predicting")):
                                    try:
                                        final_results = []
                                        sdf_files_list = list(batch_docking_dir.glob("*.sdf"))

                                        progress_bar = st.progress(0)
                                        total_files = len(sdf_files_list)
                                        log_messages = []

                                        for i, sdf_file in enumerate(sdf_files_list):
                                            try:
                                                # 改进的文件名解析
                                                stem = sdf_file.stem
                                                parts = stem.split("_", 1)
                                                if len(parts) < 2:
                                                    raise ValueError("文件名格式错误")
                                                    
                                                receptor_name = parts[0]
                                                ligand_part = parts[1].replace("_docked", "")
                                                
                                                pdb_file_name = f"{receptor_name}.pdb"
                                                pdb_file_path = batch_docking_dir / pdb_file_name

                                                if pdb_file_path.exists():
                                                    log_messages.append(f"正在处理：{pdb_file_name} 和 {sdf_file.name}")
                                                    
                                                    with tempfile.TemporaryDirectory() as tmpdir:
                                                        output_csv_path_tmp = Path(tmpdir) / "temp_result.csv"
                                                        
                                                        cmd = [
                                                            "python",
                                                            "./others/PLANET/pred.py",
                                                            "-p", str(pdb_file_path),
                                                            "-l", str(sdf_file),
                                                            "-m", str(sdf_file),
                                                            "-o", str(output_csv_path_tmp)
                                                        ]
                                                        
                                                        result = subprocess.run(cmd, capture_output=True, text=True)
                                                        
                                                        if result.returncode == 0 and output_csv_path_tmp.exists():
                                                            temp_df = pd.read_csv(output_csv_path_tmp)
                                                            if "Binding_Affinity" in temp_df.columns:
                                                                binding_affinity = temp_df["Binding_Affinity"].iloc[0]
                                                                final_results.append({
                                                                    "Protein_File": receptor_name,
                                                                    "Ligand_File": ligand_part,
                                                                    "Binding_Affinity": binding_affinity
                                                                })
                                                                log_messages.append(f"成功：{pdb_file_name} 和 {sdf_file.name}")
                                                            else:
                                                                log_messages.append(f"错误：{sdf_file.name} 结果文件缺少 Binding_Affinity 列")
                                                        else:
                                                            log_messages.append(f"失败：{sdf_file.name}\n错误信息：{result.stderr}")
                                                else:
                                                    log_messages.append(f"跳过：未找到对应的 {pdb_file_name}")

                                                progress_bar.progress((i+1)/total_files)
                                                
                                            except Exception as e:
                                                log_messages.append(f"处理 {sdf_file.name} 时发生错误：{str(e)}")

                                        if final_results:
                                            results_df = pd.DataFrame(final_results)

                                            # 保存到session state
                                            st.session_state.affinity_results_df = results_df
                                            st.session_state.prediction_completed = True

                                            st.success(t("affinity.success_batch_complete"))
                                            st.dataframe(results_df)

                                            # 提供下载
                                            csv_data = results_df.to_csv(index=False)
                                            st.download_button(
                                                label=t("affinity.download_batch_result"),
                                                data=csv_data,
                                                file_name="batch_prediction_results.csv",
                                                mime="text/csv"
                                            )
                                        else:
                                            st.error(t("affinity.error_no_result"))

                                        # 显示日志
                                        with st.expander(t("affinity.view_log")):
                                            st.text_area("Log Details", value="\n".join(log_messages), height=300)

                                    except Exception as e:
                                        st.error(t("affinity.error_batch_failed", error=str(e)))

    with tab2:
        st.subheader(t("affinity.data_subtitle"))

        if st.session_state.affinity_results_df is not None:
            df = st.session_state.affinity_results_df

            # 显示数据统计
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Records", len(df))
            with col2:
                if 'Binding_Affinity' in df.columns:
                    st.metric("Average Affinity", f"{df['Binding_Affinity'].mean():.2f}")
            with col3:
                if 'Binding_Affinity' in df.columns:
                    st.metric("Affinity Range", f"{df['Binding_Affinity'].min():.2f} ~ {df['Binding_Affinity'].max():.2f}")

            # 显示完整数据
            st.dataframe(df, use_container_width=True)

            # 提供数据编辑功能
            st.subheader(t("affinity.edit_title"))
            edited_df = st.data_editor(df, use_container_width=True)

            if st.button(t("affinity.button_update")):
                st.session_state.affinity_results_df = edited_df
                st.success(t("affinity.success_updated"))

        else:
            st.info(t("affinity.info_no_data"))

    with tab3:
        st.subheader(t("affinity.heatmap_subtitle"))

        if st.session_state.affinity_results_df is not None:
            df = st.session_state.affinity_results_df

            # 热图配置选项
            st.subheader(t("affinity.heatmap_config"))
            
            col1, col2 = st.columns(2)

            with col1:
                # 热图样式选项
                colormap = st.selectbox(t("affinity.colormap_label"),
                    ["viridis", "coolwarm", "RdYlBu_r", "plasma", "inferno", "magma", "RdBu_r", "Spectral"])

                show_values = st.checkbox("Show Values", value=True)

            with col2:
                # 图片尺寸
                width = st.slider("Image Width", 6, 20, 10)
                height = st.slider("Image Height", 4, 16, 8)

            # 热图命名
            st.subheader(t("affinity.heatmap_naming"))
            heatmap_title = st.text_input(t("affinity.heatmap_title_label"), value=t("affinity.heatmap_title_default"),
                                        help=t("affinity.help_heatmap_title"))
            file_name = st.text_input(t("affinity.heatmap_filename_label"), value=t("affinity.heatmap_filename_default"),
                                    help=t("affinity.help_heatmap_filename"))

            # 高级选项
            with st.expander(t("affinity.advanced_options")):
                # 色条范围设置（解决多次预测对比问题）
                st.write(t("affinity.colorbar_range"))
                col_a, col_b = st.columns(2)
                with col_a:
                    use_custom_range = st.checkbox("Use Custom Color Bar Range",
                                                  help="Check to fix color bar range for comparing multiple predictions")
                
                if use_custom_range and 'Binding_Affinity' in df.columns:
                    current_min = float(df['Binding_Affinity'].min())
                    current_max = float(df['Binding_Affinity'].max())
                    with col_b:
                        st.write(t("affinity.current_range", min=current_min, max=current_max))

                    col_c, col_d = st.columns(2)
                    with col_c:
                        vmin = st.number_input("Color Bar Min", value=current_min, step=0.1)
                    with col_d:
                        vmax = st.number_input("Color Bar Max", value=current_max, step=0.1)
                else:
                    vmin, vmax = None, None

                # 排序选项
                st.write(t("affinity.sort_options"))
                sort_by_protein = st.checkbox("Sort by Protein Name")
                sort_by_ligand = st.checkbox("Sort by Ligand Name")
                
                filtered_df = df  # 不再过滤数据
                
            # 生成热图按钮
            if st.button(t("affinity.button_generate"), type="primary"):
                try:
                    # 使用固定的列名（和原始代码保持一致）
                    protein_col = "Protein_File"
                    ligand_col = "Ligand_File"
                    value_col = "Binding_Affinity"

                    # 检查必需的列是否存在
                    required_cols = [protein_col, ligand_col, value_col]
                    missing_cols = [col for col in required_cols if col not in df.columns]
                    if missing_cols:
                        st.error(t("affinity.error_missing_cols", cols=missing_cols))
                        st.stop()
                    
                    # 准备数据
                    plot_df = filtered_df.copy()
                    
                    # 创建透视表
                    heatmap_data = plot_df.pivot(
                        index=protein_col, 
                        columns=ligand_col, 
                        values=value_col
                    )
                    
                    # 应用排序
                    if sort_by_protein:
                        heatmap_data = heatmap_data.sort_index()
                    if sort_by_ligand:
                        heatmap_data = heatmap_data.sort_index(axis=1)
                    
                    # 使用 Matplotlib 绘制热图
                    plt.figure(figsize=(width, height), dpi=600)
                    
                    # 设置色条范围
                    vmin_plot = vmin if use_custom_range else None
                    vmax_plot = vmax if use_custom_range else None
                    
                    # 创建热图
                    sns.heatmap(
                        heatmap_data, 
                        annot=show_values, 
                        cmap=colormap, 
                        fmt=".2f",
                        square=False,
                        vmin=vmin_plot,
                        vmax=vmax_plot
                    )
                    
                    # 使用用户自定义的标题
                    plt.title(heatmap_title, fontsize=14, pad=20)
                    plt.xlabel("Ligands", fontsize=12)
                    plt.ylabel("Proteins", fontsize=12)
                    plt.xticks(rotation=45, ha='right')
                    plt.yticks(rotation=0)
                    plt.tight_layout()
                    
                    st.pyplot(plt)
                    
                    # 保存图片，使用用户自定义的文件名
                    img_buffer = io.BytesIO()
                    plt.savefig(img_buffer, format='png', dpi=600, bbox_inches='tight')
                    img_buffer.seek(0)
                    
                    # 清理文件名（移除特殊字符）
                    clean_filename = "".join(c for c in file_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    if not clean_filename:
                        clean_filename = "heatmap"
                    
                    st.download_button(
                        label=t("affinity.download_heatmap"),
                        data=img_buffer,
                        file_name=f"{clean_filename}.png",
                        mime="image/png",
                        use_container_width=True
                    )

                except Exception as e:
                    st.error(t("affinity.error_heatmap", error=str(e)))

            # 数据统计图表
            st.subheader(t("affinity.data_stats"))
            if 'Binding_Affinity' in df.columns:
                col1, col2 = st.columns(2)
                
                with col1:
                    # 直方图
                    fig, ax = plt.subplots(figsize=(8, 6))
                    ax.hist(df['Binding_Affinity'], bins=20, alpha=0.7, edgecolor='black')
                    ax.set_xlabel('Binding Affinity')
                    ax.set_ylabel('Frequency')
                    ax.set_title('Binding Affinity Distribution Histogram')
                    st.pyplot(fig)
                
                with col2:
                    # 箱线图
                    fig, ax = plt.subplots(figsize=(8, 6))
                    ax.boxplot(df['Binding_Affinity'])
                    ax.set_ylabel('Binding Affinity')
                    ax.set_title('Binding Affinity Box Plot')
                    st.pyplot(fig)

        else:
            st.info(t("affinity.info_no_data"))




# ------------------------------------------------------------------------------
# 任务管理
# ------------------------------------------------------------------------------
elif page == "task_manager":
    from pathlib import Path

    st.title(t("task.title"))

    JOBS_DIR = Path("./jobs")

    if not JOBS_DIR.exists() or not any(JOBS_DIR.iterdir()):
        st.info(t("task.info_no_jobs"))
    else:
        # 扫描所有任务，读取状态
        jobs = []
        for job_path in JOBS_DIR.iterdir():
            if not job_path.is_dir():
                continue
            status_file = job_path / "status.json"
            if status_file.exists():
                with open(status_file) as f:
                    status = json.load(f)
            else:
                status = {"state": "unknown", "progress": 0, "log": []}
            jobs.append({"id": job_path.name, "state": status["state"], "status": status, "path": job_path})

        if not jobs:
            st.info("No task records found.")
        else:
            # 状态图标映射
            state_icons = {"completed": "✅", "running": "🔄", "failed": "❌", "unknown": "❓"}

            # 排序选项
            col_sort1, col_sort2 = st.columns([1, 1])
            with col_sort1:
                sort_by = st.radio(t("task.sort_by"), [t("task.sort_time"), t("task.sort_name")], horizontal=True, key="job_sort_by")
            with col_sort2:
                sort_order = st.radio(t("task.sort_order"), [t("task.sort_new_to_old"), t("task.sort_old_to_new")], horizontal=True, key="job_sort_order")

            reverse = (sort_order == t("task.sort_new_to_old"))
            if sort_by == t("task.sort_time"):
                jobs.sort(key=lambda j: j["status"].get("start_time", ""), reverse=reverse)
            else:
                jobs.sort(key=lambda j: j["id"], reverse=reverse)

            st.subheader(t("task.count_jobs", count=len(jobs)))

            for i, job in enumerate(jobs):
                status = job["status"]
                icon = state_icons.get(job["state"], "❓")
                time_str = status.get("start_time", t("task.unknown_time"))
                label = f"{icon} {job['id']}　|　{time_str}　|　{job['state'].upper()}"

                with st.expander(label, expanded=False):
                    job_dir = job["path"]

                    # 时间信息
                    if "end_time" in status:
                        st.write(t("task.complete_time", time=status['end_time']))

                    # 下载 + 可视化（仅已完成任务）
                    zip_path = job_dir / "results" / "docking_results.zip"
                    if zip_path.exists() and job["state"] == "completed":
                        st.download_button(
                            t("task.download_result"),
                            data=zip_path.read_bytes(),
                            file_name=f"results_{job['id']}.zip",
                            use_container_width=True,
                            key=f"dl_{job['id']}"
                        )

                        st.markdown(t("task.visualization"))
                        with zipfile.ZipFile(zip_path, 'r') as zf:
                            docked_sdfs = [n for n in zf.namelist() if n.endswith("_docked.sdf")]

                        if docked_sdfs:
                            selected_sdf = st.selectbox(
                                t("task.select_result"), docked_sdfs, key=f"vis_sel_{job['id']}")

                            if st.button(t("task.view_3d"), key=f"vis_btn_{job['id']}"):
                                pdb_match = None
                                for pdb_f in sorted((job_dir / "uploads").glob("*.pdb"),
                                                    key=lambda p: len(p.stem), reverse=True):
                                    if selected_sdf.startswith(pdb_f.stem + "_"):
                                        pdb_match = pdb_f
                                        break

                                if pdb_match:
                                    vis_dir = job_dir / "vis_tmp"
                                    vis_dir.mkdir(exist_ok=True)
                                    with zipfile.ZipFile(zip_path, 'r') as zf:
                                        (vis_dir / selected_sdf).write_bytes(zf.read(selected_sdf))
                                    st_molstar_docking(
                                        str(pdb_match),
                                        str(vis_dir / selected_sdf),
                                        key=f"vis_mol_{job['id']}_{selected_sdf}",
                                        height=600
                                    )
                                else:
                                    st.error(t("task.error_no_pdb"))
                        else:
                            st.info(t("task.info_no_results"))

                    # 日志
                    if status.get("log"):
                        st.markdown(t("task.log"))
                        st.text("\n".join(status["log"]))


# ------------------------------------------------------------------------------
# 作者信息
# ------------------------------------------------------------------------------
if page == "author":
    # 使用 HTML 和 Markdown 居中标题
    st.markdown(
        "<h1 style='text-align: center;'>👽小闪电-FLASH⚡️</h1>",
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # 显示原作者图片
    st.markdown(t("author.title"))
    if os.path.exists("./others/author.png"):
        st.image("./others/author.png", use_container_width=True)
    else:
        st.error(t("author.error_image"))

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")

    # 显示贡献者信息
    st.markdown(t("author.modified_title"))
    if os.path.exists("./others/author2.png"):
        st.image("./others/author2.png", use_container_width=True)
    else:
        st.error(t("author.modified_error"))