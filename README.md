**🌐 Language / 言語:** **中文** | [English](README.en.md) | [日本語](README.ja.md)

# FLASH_DOCK ⚡️

> 基于 AI 的一站式分子对接平台 | AI-Powered Molecular Docking Platform
>
> 🌐 应用内置多语言支持（中文 / English / 日本語），可在侧边栏切换

FLASH_DOCK 是一个基于 Streamlit 的计算化学 Web 应用，把**配体准备 → 口袋检测 → 分子对接 → 亲和力预测**整条流程做成一个开箱即用的图形界面。

本项目 Fork 自 [Neo-Flash/FLASH_DOCK](https://github.com/Neo-Flash/FLASH_DOCK)，并在其基础上重构。

---

## 本版本（by Nuki）的主要改动

| 改动项 | 说明 |
|--------|------|
| **口袋检测换成 Pokeformer** | 用图 Transformer + fpocket 的 [Pokeformer](https://github.com/pfnet-research/pocket_detection) 替换原 P2Rank，输出按集成评分排序的口袋及中心坐标（去掉了 Java 依赖） |
| **界面现代化重构** | 统一的「科学仪器」视觉系统：流水线分阶段页头、等宽字体呈现坐标/评分、图标导航、卡片式布局 |
| **开箱即用 · 单一环境** | 新增 `environment.yml`，`setup.sh` 一键创建**一个** conda 环境（应用 + Pokeformer）并自动下载权重 |
| **代码瘦身** | 去除重复横幅与冗余 import，抽出 `ui/`（主题与组件）和 `pocket/`（Pokeformer 适配层）模块 |
| **任务管理 + 批量可视化** | 集中查看后台对接任务，批量页内置 3D 可视化 |
| **多语言 (i18n)** | 中 / 英 / 日 三语，侧边栏一键切换，翻译位于 `lang/` |

> 未来计划：让筛选更大更快，先支持 **Apple 原生加速 (MPS)**、再支持 **NVIDIA (CUDA)**。当前推理设备已可配置（CPU / MPS / CUDA），加速将在后续版本完善。

---

## 功能概览

| # | 模块 | 说明 |
|---|------|------|
| 1 | **准备配体** | 上传 SDF / 在线绘制（Ketcher）/ 输入 SMILES，自动生成优化 3D 构象（ETKDG + MMFF），支持 CSV 批量 |
| 2 | **口袋检测** | 基于 Pokeformer 自动定位结合口袋，输出口袋中心坐标 CSV，可直接用于对接（单个 + 批量） |
| 3 | **分子对接** | 基于 Uni-Mol Docking v2，自动读取口袋 CSV 或手动设置对接盒子 |
| 4 | **批量分子对接** | 多蛋白 × 多配体后台异步对接，UUID 任务追踪，结果打包 ZIP |
| 5 | **预测亲和力** | 基于 PLANET 预测结合亲和力，含数据查看与热图生成 |
| 6 | **任务管理** | 集中查看所有后台任务状态，下载结果并做 3D 可视化 |

---

## 架构：一个环境跑全部

整个项目使用**单一 conda 环境 `flashdock`**（Python 3.10），界面与 Pokeformer 口袋检测共用它；Pokeformer 仍以**子进程**调用（与 Uni-Mol、PLANET 一致），便于隔离与未来加速。

关键依赖：`torch 2.5.x`、`PyG 2.5.3`、`pytorch_scatter/cluster`、`fpocket 4.2`、`rdkit`、`streamlit` 等，全部来自 `environment.yml`。

> 为什么是 torch 2.5.x：Pokeformer 需要 `pytorch_scatter/cluster`，在 Apple Silicon 上只有 conda-forge 提供，且只与 `torch<2.6` 稳定配对（2.5.x 同时保留安全的 `torch.load` 默认并自带 MPS）。这是同一环境里能**同时**满足应用与 Pokeformer 的最新版本。

---

## 快速开始（一键安装）

### 前置条件

- **conda 或 mamba**（推荐 [Miniforge](https://github.com/conda-forge/miniforge)）
- **Python 3.9+**
- GPU 可选：NVIDIA CUDA 会自动启用；Apple Silicon 走 MPS/CPU

> 不再需要 Java —— 口袋检测已改用 fpocket（由 `setup.sh` 装进隔离环境）。

### 安装步骤

```bash
# 1. 克隆
git clone https://github.com/AIChemist-Nuki/FLASH_DOCK.git
cd FLASH_DOCK

# 2. 一键安装并启动（可选：传入 Uni-Mol 权重路径）
bash setup.sh /path/to/unimol_docking_v2_240517.pt
```

`setup.sh` 会自动：
- 检测 conda/mamba 与硬件（CUDA / Apple MPS / CPU）
- 用 `environment.yml` 创建**单一**环境 `flashdock`（应用 + Pokeformer + fpocket）
- 尽力安装 Uni-Core（对接所需）
- 下载并解压 Pokeformer 权重（Zenodo，约 396MB），放置 Uni-Mol 权重、检查 PLANET
- 打印安装总结并启动应用

启动后浏览器打开 `http://localhost:8501`。

### 后续启动

```bash
conda activate flashdock
streamlit run app.py     # 或再次 bash setup.sh（跳过已装项）
```

---

## 模型文件说明

| 模型 | 大小 | 是否随仓库 | 用途 | 获取方式 |
|------|------|-----------|------|----------|
| `unimol_docking_v2_240517.pt` | 465MB | ❌ 需下载 | 分子对接 | [Uni-Mol Releases](https://github.com/deepmodeling/Uni-Mol/releases) |
| `fold0~4_best_model.pt` | 共 ~396MB | ❌ 需下载 | 口袋检测（Pokeformer） | Zenodo [10.5281/zenodo.13070037](https://doi.org/10.5281/zenodo.13070037)（`setup.sh` 自动下载） |
| `PLANET.param` | 18MB | ✅ 已含 | 亲和力预测 | — |

---

## 手动安装（脚本不适用时）

<details><summary>点击展开</summary>

```bash
# 1. 单一环境（含 torch / PyG / pytorch_scatter+cluster / fpocket / rdkit / streamlit）
conda env create -f environment.yml && conda activate flashdock

# 2. 对接需要 Uni-Core（亲和力需要 DGL；按需安装）
pip install ninja && pip install ./others/Uni-Core

# 3. 权重
#  - Uni-Mol：放到 others/Uni-Mol/unimol_docking_v2/unimol_docking_v2_240517.pt
#  - Pokeformer：从 Zenodo 下载 best_models.tar.xz 解压到
#    others/pocket_detection/examples/   （得到 fold0~4_best_model.pt）

# 4. 启动
streamlit run app.py
```

</details>

---

## 使用教程

典型流程：**准备配体 → 口袋检测 → 分子对接 →（批量）→ 预测亲和力**。主页可「下载示例文件」。

### Step 1 · 准备配体
上传 SDF、用 Ketcher 绘制、或输入 SMILES；系统生成优化 3D 构象（ETKDG + MMFF）并可下载 SDF。批量页支持含 `mol_name`、`smiles` 两列的 CSV。

### Step 2 · 口袋检测（Pokeformer）
- **单个蛋白**：上传 PDB → 「开始口袋预测」→ 查看排序后的口袋（含中心坐标）→ 下载 `best_pocket.csv`。
- **批量蛋白**：一次上传多个 PDB → 下载汇总 CSV（含 `Protein File / rank / center_x/y/z`），**供批量对接直接使用**。
- 也可「加载示例蛋白」快速体验。

> 口袋中心来自 fpocket 候选口袋的几何中心，排序用 Pokeformer 的集成评分（越高越好）。

### Step 3 · 分子对接
上传蛋白 PDB + 配体 SDF；上传口袋 CSV 可自动填充中心坐标，也可手动设置盒子；点击「开始对接」，完成后 3D 可视化并下载结果。

### Step 4 · 批量对接
先上传**批量口袋 CSV**，再上传所有蛋白与配体；系统生成「蛋白 × 配体」任务表，可编辑 `Run` 列控制运行项；提交后记下**任务 ID**，后台异步执行。

### Step 5 · 任务管理 / 预测亲和力
在「任务管理」集中查看状态（✅/🔄/❌）、下载结果并可视化；在「预测亲和力」用 PLANET 单个/批量预测，并生成蛋白–配体亲和力热图。

---

## 常见问题

**Q：口袋检测报错找不到 fpocket 或权重缺失？**
A：确认已用 `setup.sh` 或 `environment.yml` 创建 `flashdock` 环境，且 `others/pocket_detection/examples/` 下有 `fold0~4_best_model.pt`。如需用别的环境跑 Pokeformer，可设 `FLASHDOCK_POCKET_PYTHON` 指定其 python。

**Q：对接很慢？**
A：Uni-Mol 在 CPU 上较慢，建议用 CUDA GPU；Apple 加速在后续版本支持。

**Q：批量对接任务一直 `running`？**
A：查看终端报错，常见是模型权重缺失或路径不对。

**Q：`Uni-Core` 安装失败？**
A：先 `pip install ninja`，确保 torch 与 CUDA 匹配；可试 `pip install --no-build-isolation ./others/Uni-Core`。

---

## 使用的 AI 算法

| 算法 | 用途 | 论文 / 仓库 |
|------|------|------|
| [Uni-Mol Docking v2](https://arxiv.org/abs/2405.11769) | 分子对接 | Towards Accurate and Efficient Molecular Docking |
| [Pokeformer](https://github.com/pfnet-research/pocket_detection) | 口袋检测 | Ishitani et al., *Protein ligand binding site prediction using graph transformer neural network* |
| [PLANET](https://pubs.acs.org/doi/10.1021/acs.jcim.3c00253) | 亲和力预测 | Protein-Ligand Binding Affinity Prediction |

---

## 项目结构

```
FLASH_DOCK/
├── app.py                      # 主程序（streamlit run app.py）
├── environment.yml             # 单一 conda 环境（应用 + Pokeformer）
├── requirements.txt            # （参考）pip 层
├── setup.sh                    # 一键安装与启动
├── .streamlit/config.toml      # 主题
├── ui/                         # 界面工具包（主题 + 组件）
│   └── theme.py
├── pocket/                     # Pokeformer 适配层
│   └── pokeformer.py
├── lang/                       # i18n（zh / en / ja）
├── Batch_Docking/              # 批量对接示例输入
├── examples/                   # 示例数据（examples.zip）
└── others/                     # 第三方工具与模型
    ├── Uni-Mol/                #   分子对接（权重需下载）
    ├── pocket_detection/       #   Pokeformer（权重需下载）
    ├── PLANET/                 #   亲和力预测（含 PLANET.param）
    └── Uni-Core/               #   PyTorch 底层框架
```

---

## 致谢

- 原项目：[小闪电-FLASH (Neo-Flash)](https://github.com/Neo-Flash/FLASH_DOCK)
- [Uni-Mol Docking v2](https://github.com/deepmodeling/Uni-Mol) · 分子对接引擎
- [Pokeformer](https://github.com/pfnet-research/pocket_detection)（Preferred Networks）· 口袋检测
- [PLANET](https://github.com/ComputArtCMCG/PLANET) · 亲和力预测
- [fpocket](https://github.com/Discngine/fpocket) · 口袋候选检测
- [Streamlit](https://streamlit.io/) · Web 应用框架

---

## 作者与贡献者

**原作者**：小闪电-FLASH (Neo-Flash) — 华东理工大学 药学院 / 华东师范大学 计算机科学与技术学院 · [GitHub](https://github.com/Neo-Flash)

**修改与优化**：Nuki — 东京科学大学 · ma240306@tmd.ac.jp

---

## License

本项目基于 [Neo-Flash/FLASH_DOCK](https://github.com/Neo-Flash/FLASH_DOCK) 修改；Pokeformer 采用 MIT 许可。请遵循各上游项目的许可协议。
