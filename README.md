**🌐 Language / 言語:** **中文** | [English](README.en.md) | [日本語](README.ja.md)

# FLASH_DOCK ⚡️

> 基于 AI 的一站式分子对接平台 | AI-Powered Molecular Docking Platform
>
> 🌐 应用内置多语言支持（中文 / English / 日本語），可在侧边栏切换

FLASH_DOCK 是一个基于 Streamlit 构建的计算化学 Web 应用，集成了配体准备、口袋预测、分子对接、结合亲和力预测等功能，为药物发现研究提供开箱即用的图形化界面。

本项目 Fork 自 [Neo-Flash/FLASH_DOCK](https://github.com/Neo-Flash/FLASH_DOCK)，在原版基础上进行了功能扩展和优化。

---

## 与原版的主要差异

本版本（by Nuki）在原版基础上新增和优化了以下内容：

| 改动项 | 说明 |
|--------|------|
| **任务管理模块** | 全新的「任务管理」页面，可查看所有后台对接任务的状态（完成/运行中/失败），支持按时间或名称排序，直接下载结果包和查看3D可视化 |
| **批量对接结果可视化** | 在批量分子对接页面中新增了对接结果的3D可视化功能，自动匹配蛋白PDB与配体SDF进行展示 |
| **任务数量限制** | 新增批量对接任务数量上限校验（200个），避免服务器过载 |
| **任务日志增强** | 每个对接任务都有详细的运行日志，记录坐标信息、成功/失败状态 |
| **多语言支持 (i18n)** | 新增中文/英语/日语三语支持，侧边栏一键切换，翻译文件位于 `lang/` 目录，可轻松扩展新语言 |
| **代码结构优化** | 去除密码嵌套后重构代码结构，代码更清晰易读 |

---

## 功能概览

FLASH_DOCK 提供 **6 个功能模块**，覆盖从配体准备到亲和力分析的完整流程：

### 1. 准备配体
上传 SDF 文件、在线绘制分子（Ketcher）、或直接输入 SMILES，系统自动生成优化后的 3D 构象（ETKDG + MMFF 力场）。支持批量处理 CSV 文件中的 SMILES 数据。

### 2. 口袋预测
基于 P2Rank 算法自动预测蛋白质结合口袋，支持单个和批量蛋白预测，输出口袋中心坐标 CSV 文件，可直接用于后续对接。

### 3. 分子对接
基于 Uni-Mol Docking v2 模型，上传蛋白（PDB）和配体（SDF），自动读取口袋预测 CSV 填充对接参数，也支持手动调整对接盒子。

### 4. 批量分子对接
多蛋白 × 多配体的批量对接，后台异步处理不阻塞页面，UUID 任务 ID 追踪，自动打包结果为 ZIP 文件。

### 5. 预测亲和力
基于 PLANET 模型预测结合亲和力，支持单个和批量预测，三个选项卡：亲和力预测 / 数据查看 / 热图生成。

### 6. 任务管理（新增）
集中查看所有后台对接任务，状态图标（✅🔄❌），按时间/名称排序，一键下载结果包，3D 可视化对接结果。

---

## 快速开始（一键安装）

### 前置条件

开始之前请确保系统已安装：
- **Python 3.8+**
- **Java 8+**（P2Rank 口袋预测需要。安装方法：Ubuntu `sudo apt install default-jdk` / macOS `brew install openjdk`）
- **CUDA GPU**（可选但强烈推荐，大幅加速对接计算）

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/AIChemist-Nuki/FLASH_DOCK.git
cd FLASH_DOCK

# 2. 下载 Uni-Mol Docking v2 模型权重（约 465MB）
#    下载地址: https://github.com/deepmodeling/Uni-Mol/releases
#    找到 unimol_docking_v2_240517.pt 下载到任意位置

# 3. 创建虚拟环境（推荐）
conda create -n flashdock python=3.9 -y
conda activate flashdock

# 4. 一键安装并启动（传入模型权重路径）
bash setup.sh /path/to/unimol_docking_v2_240517.pt
```

`setup.sh` 会自动完成以下所有事情：
- 检测系统环境（Python、Java、CUDA）
- 将模型权重复制到正确位置
- 安装 PyTorch（自动适配 CUDA/CPU）
- 编译安装 Uni-Core 框架
- 安装全部 Python 依赖
- 检查 P2Rank 和 PLANET 模型
- 打印安装状态总结
- 启动 Streamlit 应用

启动成功后浏览器会自动打开 `http://localhost:8501`。

### 后续启动

首次安装完成后，以后只需：

```bash
conda activate flashdock
bash setup.sh
```

脚本会跳过已安装的依赖，直接启动应用。

---

### 手动安装（如果脚本不适用）

<details>
<summary>点击展开手动安装步骤</summary>

#### 1. 安装 PyTorch

根据硬件环境到 https://pytorch.org/get-started/locally/ 获取安装命令：

```bash
# 有 CUDA GPU:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
# 仅 CPU:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

#### 2. 安装 Uni-Core

```bash
pip install ninja
cd others/Uni-Core
pip install .
cd ../..
```

如果编译报错，参考 [Uni-Core 官方仓库](https://github.com/dptech-corp/Uni-Core)。

#### 3. 安装其他依赖

```bash
pip install streamlit streamlit-molstar streamlit-ketcher py3Dmol stmol
pip install rdkit-pypi pandas numpy scipy scikit-learn matplotlib seaborn
pip install tqdm lmdb sh biopandas
```

#### 4. 放置模型权重

将下载的 `unimol_docking_v2_240517.pt` 放到：

```
others/Uni-Mol/unimol_docking_v2/unimol_docking_v2_240517.pt
```

#### 5. 确保 P2Rank 可执行

```bash
chmod +x others/p2rank_2.5/prank
```

#### 6. 启动

```bash
streamlit run FlashDock_0315.py
```

</details>

---

### 模型文件说明

| 模型 | 大小 | 包含在仓库中？ | 用途 |
|------|------|----------------|------|
| `unimol_docking_v2_240517.pt` | 465MB | ❌ 需自行下载 | 分子对接（核心功能） |
| `PLANET.param` | 18MB | ✅ 已包含 | 亲和力预测 |
| `p2rank_2.5/` | 292MB | ✅ 已包含 | 口袋预测 |

Uni-Mol 模型下载地址：[Uni-Mol Releases](https://github.com/deepmodeling/Uni-Mol/releases)

---

## 使用教程

### 典型工作流程

```
准备配体 → 口袋预测 → 分子对接 → 预测亲和力
```

下面以一个完整的分子对接实验为例，走通全流程。项目内置了示例文件，可以在主页点击「下载示例文件」获取。

---

### Step 1: 准备配体

> 目的：将小分子转换为带有优化 3D 构象的 SDF 文件

**方法 A：上传 SDF 文件**
1. 点击侧边栏「准备配体」
2. 在「单分子处理」选项卡中上传 SDF 文件
3. 系统自动展示 2D 和 3D 分子结构
4. 点击「下载3D分子的SDF文件」保存结果

**方法 B：绘制分子或输入 SMILES**
1. 在 Ketcher 编辑器中绘制分子结构，或直接粘贴 SMILES 字符串
2. 系统自动生成 3D 构象（ETKDG 算法 + MMFF 力场优化）
3. 下载生成的 SDF 文件

**方法 C：批量处理**
1. 切换到「批量处理」选项卡
2. 上传包含 SMILES 列的 CSV 文件
3. 系统批量生成所有分子的 3D 结构
4. 下载结果

---

### Step 2: 口袋预测

> 目的：找到蛋白质上最可能与小分子结合的位点（口袋）

**单个蛋白：**
1. 点击侧边栏「口袋预测」
2. 选择「单个蛋白质口袋预测」
3. 上传蛋白质 PDB 文件（或选择「加载示例蛋白」快速体验）
4. 系统调用 P2Rank 预测口袋位置
5. 查看口袋中心坐标表格，记住 rank1 口袋的坐标

**批量蛋白：**
1. 选择「批量蛋白口袋预测」
2. 一次上传多个 PDB 文件
3. 点击「开始批量预测」
4. 下载汇总的口袋预测 CSV 文件 — **后续批量对接需要用到这个文件**

---

### Step 3: 分子对接

#### 单个对接

1. 点击侧边栏「分子对接」
2. 上传蛋白质 PDB 和配体 SDF 文件
3. 设置对接网格参数：
   - 如果之前做过口袋预测，上传 CSV 文件可自动填充坐标
   - 也可以手动输入中心坐标（center_x/y/z）和盒子大小（size_x/y/z）
4. 点击「开始对接」
5. 等待计算完成（通常几分钟），查看 3D 可视化结果
6. 下载对接结果 SDF 文件

#### 批量对接

1. 点击侧边栏「批量分子对接」
2. 先上传之前生成的**批量口袋预测 CSV 文件**
3. 再上传所有蛋白质（PDB）和配体（SDF）文件
4. 系统自动生成对接任务列表（每个蛋白 × 每个配体 = 一个任务）
5. 下载任务 CSV 模板，可以编辑 `Run` 列为 `Yes/No` 控制哪些需要运行
6. 上传修改后的 CSV，点击「开始批量对接」
7. **记住任务 ID**（格式如 `a690c342`），后台会异步执行

---

### Step 4: 查看与管理任务

**方法 A：在「批量分子对接」页面查询**
1. 在页面顶部的「任务查询」区域输入任务 ID
2. 查看状态、日志、下载结果包

**方法 B：在「任务管理」页面集中查看**
1. 点击侧边栏「任务管理」
2. 查看所有历史任务列表（✅ 完成 / 🔄 运行中 / ❌ 失败）
3. 按时间或名称排序
4. 展开任务查看详细日志
5. 下载结果 ZIP 包
6. 选择具体对接结果进行 3D 可视化

---

### Step 5: 预测亲和力

> 目的：评估蛋白质-配体的结合强度

1. 点击侧边栏「预测亲和力」
2. 在「亲和力预测」选项卡中：
   - 单个预测：上传一对 PDB + SDF 文件
   - 批量预测：上传多个蛋白和配体文件，系统通过文件名自动匹配
3. 在「数据查看」选项卡中：
   - 查看预测结果表格
   - 数据分布直方图和箱线图
   - 下载 CSV 结果
4. 在「热图生成」选项卡中：
   - 自定义热图配色方案、尺寸、色条范围
   - 生成蛋白-配体亲和力矩阵热图
   - 下载热图图片

---

## 常见问题

**Q: 启动后页面空白或报错 `ModuleNotFoundError`**
A: 检查是否激活了正确的虚拟环境，并确认所有 pip 依赖已安装。

**Q: 口袋预测报错 `java: command not found`**
A: P2Rank 依赖 Java 运行环境，请安装 JDK 8 或更高版本。

**Q: 对接计算非常慢**
A: Uni-Mol Docking v2 在 CPU 上运行较慢，强烈建议使用 CUDA GPU。单个对接任务在 GPU 上通常几分钟，CPU 上可能需要更长时间。

**Q: 批量对接任务状态一直显示 `running`**
A: 检查终端是否有报错信息。常见原因是模型文件缺失或路径不正确。

**Q: `Uni-Core` 安装失败**
A: 确保已安装 `ninja`（`pip install ninja`），且 PyTorch 版本与 CUDA 版本匹配。也可以尝试 `pip install --no-build-isolation .`。

---

## 使用的 AI 算法

| 算法 | 用途 | 论文 |
|------|------|------|
| [Uni-Mol Docking v2](https://arxiv.org/abs/2405.11769) | 分子对接 | Towards Accurate and Efficient Molecular Docking |
| [P2Rank](https://jcheminf.biomedcentral.com/articles/10.1186/s13321-018-0285-8) | 口袋预测 | P2Rank: machine learning based tool for rapid and accurate prediction of ligand binding sites |
| [PLANET](https://pubs.acs.org/doi/10.1021/acs.jcim.3c00253) | 亲和力预测 | Protein-Ligand Binding Affinity Prediction |

---

## 项目结构

```
FLASH_DOCK/
├── FlashDock_0315.py              # 主程序（最新版本，直接运行这个）
├── FlashDock_web.py               # 原版 Web 程序（参考用）
├── README.md
├── Batch_Docking/                 # 批量对接示例输入文件
│   ├── receptor1~4.pdb
│   └── ligand1~4.sdf
├── Result/                        # 单次运行结果输出目录
│   ├── Binding_Affinity/
│   ├── Docking_Result/
│   ├── Predict_Pocket/
│   └── Prepare_Ligand/
├── jobs/                          # 后台任务目录（自动生成，可清空）
├── examples/                      # 示例数据
│   └── examples.zip
└── others/                        # 第三方工具和模型
    ├── Uni-Mol/                   # Uni-Mol 对接模型
    │   └── unimol_docking_v2/
    │       ├── interface/demo.py  # 对接入口脚本
    │       └── *.pt              # 模型权重（需下载）
    ├── PLANET/                    # 亲和力预测模型
    │   ├── pred.py               # 预测入口脚本
    │   └── PLANET.param          # 模型参数（需下载）
    ├── p2rank_2.5/                # 口袋预测工具
    │   └── prank                  # 可执行文件（需 Java）
    ├── Uni-Core/                  # PyTorch 底层框架
    ├── flashdock.png              # 应用 Logo
    ├── author.png                 # 原作者信息
    └── author2.png                # 贡献者信息
```

---

## 致谢

- 原项目作者：[小闪电-FLASH (Neo-Flash)](https://github.com/Neo-Flash/FLASH_DOCK)
- [Uni-Mol Docking v2](https://github.com/deepmodeling/Uni-Mol) - 分子对接引擎
- [P2Rank](https://github.com/rdk/p2rank) - 口袋预测工具
- [PLANET](https://github.com/ComputArtCMCG/PLANET) - 亲和力预测模型
- [Streamlit](https://streamlit.io/) - Web 应用框架

---

## 作者与贡献者

**原作者**: 小闪电-FLASH (Neo-Flash)
华东理工大学 药学院 | 华东师范大学 计算机科学与技术学院
Email: 52265901016@stu.ecnu.edu.cn
GitHub: [Neo-Flash](https://github.com/Neo-Flash)

**修改与优化**: Nuki
东京医科齿科大学 (2023-2024) | 东京科学大学 (2024-2026)
Email: ma240306@tmd.ac.jp

---

## License

本项目基于 [Neo-Flash/FLASH_DOCK](https://github.com/Neo-Flash/FLASH_DOCK) 修改。请遵循原项目的许可协议。
