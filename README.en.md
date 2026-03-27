**🌐 Language / 言語:** [中文](README.md) | **English** | [日本語](README.ja.md)

# FLASH_DOCK ⚡️

> AI-Powered Molecular Docking Platform
>
> 🌐 Built-in multilingual support (中文 / English / 日本語) — switch in the sidebar

FLASH_DOCK is a computational chemistry web application built on Streamlit, integrating ligand preparation, pocket prediction, molecular docking, and binding affinity prediction functionality, providing an out-of-the-box graphical interface for drug discovery research.

This project is forked from [Neo-Flash/FLASH_DOCK](https://github.com/Neo-Flash/FLASH_DOCK) with extended functionality and optimizations based on the original version.

---

## Main Differences from the Original Version

This version (by Nuki) adds and optimizes the following based on the original:

| Item | Description |
|------|-------------|
| **Task Management Module** | New "Task Management" page to view the status of all backend docking tasks (Completed/Running/Failed), with sorting by time or name, direct result package downloads, and 3D visualization |
| **Batch Docking Result Visualization** | Added 3D visualization functionality for docking results in the batch molecular docking page, automatically matching protein PDB with ligand SDF for display |
| **Task Quantity Limit** | New validation for batch docking task quantity limit (200 tasks) to prevent server overload |
| **Task Logging Enhancement** | Each docking task has detailed run logs recording coordinate information and success/failure status |
| **Multilingual Support (i18n)** | Added Chinese/English/Japanese trilingual support with one-click sidebar switching; translation files located in `lang/` directory for easy language expansion |
| **Code Structure Optimization** | Restructured code after removing password nesting for clearer and more readable code |

---

## Feature Overview

FLASH_DOCK provides **6 functional modules**, covering the complete workflow from ligand preparation to affinity analysis:

### 1. Prepare Ligand
Upload SDF files, draw molecules online (Ketcher), or directly input SMILES strings. The system automatically generates optimized 3D conformations (ETKDG + MMFF force field). Supports batch processing of SMILES data from CSV files.

### 2. Pocket Prediction
Automatically predicts protein binding pockets based on the P2Rank algorithm, supports single and batch protein prediction, and outputs pocket center coordinate CSV files for direct use in subsequent docking.

### 3. Molecular Docking
Based on Uni-Mol Docking v2 model, upload proteins (PDB) and ligands (SDF). Automatically reads pocket prediction CSV to populate docking parameters, or manually adjust the docking box.

### 4. Batch Molecular Docking
Multi-protein × multi-ligand batch docking with asynchronous backend processing that doesn't block the page. UUID task ID tracking and automatic packaging of results as ZIP files.

### 5. Predict Affinity
Predicts binding affinity based on the PLANET model, supports single and batch prediction with three tabs: Affinity Prediction / Data View / Heatmap Generation.

### 6. Task Management (New)
Centrally view all backend docking tasks with status icons (✅🔄❌), sort by time/name, one-click result package downloads, and 3D visualization of docking results.

---

## Quick Start (One-Click Installation)

### Prerequisites

Before starting, ensure the following are installed on your system:
- **Python 3.8+**
- **Java 8+** (required for P2Rank pocket prediction. Installation: Ubuntu `sudo apt install default-jdk` / macOS `brew install openjdk`)
- **CUDA GPU** (optional but strongly recommended for significant acceleration of docking calculations)

### Installation Steps

```bash
# 1. Clone the project
git clone https://github.com/AIChemist-Nuki/FLASH_DOCK.git
cd FLASH_DOCK

# 2. Download Uni-Mol Docking v2 model weights (approximately 465MB)
#    Download address: https://github.com/deepmodeling/Uni-Mol/releases
#    Find and download unimol_docking_v2_240517.pt to any location

# 3. Create virtual environment (recommended)
conda create -n flashdock python=3.9 -y
conda activate flashdock

# 4. One-click installation and launch (pass the model weight path)
bash setup.sh /path/to/unimol_docking_v2_240517.pt
```

`setup.sh` will automatically complete all of the following:
- Detect system environment (Python, Java, CUDA)
- Copy model weights to correct location
- Install PyTorch (auto-adapts to CUDA/CPU)
- Compile and install Uni-Core framework
- Install all Python dependencies
- Check P2Rank and PLANET models
- Print installation status summary
- Launch the Streamlit application

After successful launch, the browser will automatically open `http://localhost:8501`.

### Subsequent Launches

After the first installation, you only need:

```bash
conda activate flashdock
bash setup.sh
```

The script will skip already-installed dependencies and launch the application directly.

---

### Manual Installation (if the script is not applicable)

<details>
<summary>Click to expand manual installation steps</summary>

#### 1. Install PyTorch

Go to https://pytorch.org/get-started/locally/ to obtain the installation command for your hardware environment:

```bash
# With CUDA GPU:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
# CPU only:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

#### 2. Install Uni-Core

```bash
pip install ninja
cd others/Uni-Core
pip install .
cd ../..
```

If compilation fails, refer to the [Uni-Core official repository](https://github.com/dptech-corp/Uni-Core).

#### 3. Install other dependencies

```bash
pip install streamlit streamlit-molstar streamlit-ketcher py3Dmol stmol
pip install rdkit-pypi pandas numpy scipy scikit-learn matplotlib seaborn
pip install tqdm lmdb sh biopandas
```

#### 4. Place model weights

Place the downloaded `unimol_docking_v2_240517.pt` at:

```
others/Uni-Mol/unimol_docking_v2/unimol_docking_v2_240517.pt
```

#### 5. Ensure P2Rank is executable

```bash
chmod +x others/p2rank_2.5/prank
```

#### 6. Launch

```bash
streamlit run FlashDock_0315.py
```

</details>

---

### Model File Description

| Model | Size | Included in Repository? | Purpose |
|-------|------|------------------------|---------|
| `unimol_docking_v2_240517.pt` | 465MB | ❌ Download required | Molecular docking (core functionality) |
| `PLANET.param` | 18MB | ✅ Included | Affinity prediction |
| `p2rank_2.5/` | 292MB | ✅ Included | Pocket prediction |

Uni-Mol model download address: [Uni-Mol Releases](https://github.com/deepmodeling/Uni-Mol/releases)

---

## Usage Tutorial

### Typical Workflow

```
Prepare Ligand → Pocket Prediction → Molecular Docking → Affinity Prediction
```

Below is a complete molecular docking experiment walkthrough. The project includes example files that can be downloaded by clicking "Download Example Files" on the homepage.

---

### Step 1: Prepare Ligand

> Objective: Convert small molecules to SDF files with optimized 3D conformations

**Method A: Upload SDF File**
1. Click "Prepare Ligand" in the sidebar
2. In the "Single Molecule Processing" tab, upload an SDF file
3. The system automatically displays 2D and 3D molecular structures
4. Click "Download 3D Molecule SDF File" to save results

**Method B: Draw Molecule or Input SMILES**
1. Draw molecular structure in the Ketcher editor or directly paste SMILES string
2. The system automatically generates 3D conformation (ETKDG algorithm + MMFF force field optimization)
3. Download the generated SDF file

**Method C: Batch Processing**
1. Switch to the "Batch Processing" tab
2. Upload a CSV file containing a SMILES column
3. The system batch-generates 3D structures for all molecules
4. Download the results

---

### Step 2: Pocket Prediction

> Objective: Find the most likely binding site (pocket) on the protein for small molecule interaction

**Single Protein:**
1. Click "Pocket Prediction" in the sidebar
2. Select "Single Protein Pocket Prediction"
3. Upload a protein PDB file (or select "Load Example Protein" for quick experience)
4. The system calls P2Rank to predict pocket location
5. View the pocket center coordinate table and remember the rank1 pocket coordinates

**Batch Proteins:**
1. Select "Batch Protein Pocket Prediction"
2. Upload multiple PDB files at once
3. Click "Start Batch Prediction"
4. Download the summary pocket prediction CSV file — **this file is needed for subsequent batch docking**

---

### Step 3: Molecular Docking

#### Single Docking

1. Click "Molecular Docking" in the sidebar
2. Upload protein PDB and ligand SDF files
3. Set docking grid parameters:
   - If pocket prediction was performed previously, uploading a CSV file will automatically populate coordinates
   - Or manually enter center coordinates (center_x/y/z) and box size (size_x/y/z)
4. Click "Start Docking"
5. Wait for calculation to complete (usually a few minutes) and view 3D visualization results
6. Download the docking result SDF file

#### Batch Docking

1. Click "Batch Molecular Docking" in the sidebar
2. First upload the **batch pocket prediction CSV file** generated previously
3. Then upload all protein (PDB) and ligand (SDF) files
4. The system automatically generates docking task list (each protein × each ligand = one task)
5. Download the task CSV template; you can edit the `Run` column to `Yes/No` to control which tasks to run
6. Upload the modified CSV and click "Start Batch Docking"
7. **Remember the task ID** (format like `a690c342`); the backend will execute asynchronously

---

### Step 4: View and Manage Tasks

**Method A: Query on the "Batch Molecular Docking" page**
1. Enter task ID in the "Task Query" area at the top of the page
2. View status, logs, and download result packages

**Method B: Centrally view on the "Task Management" page**
1. Click "Task Management" in the sidebar
2. View all historical task list (✅ Completed / 🔄 Running / ❌ Failed)
3. Sort by time or name
4. Expand tasks to view detailed logs
5. Download result ZIP packages
6. Select specific docking results for 3D visualization

---

### Step 5: Predict Affinity

> Objective: Assess the binding strength of protein-ligand complexes

1. Click "Predict Affinity" in the sidebar
2. In the "Affinity Prediction" tab:
   - Single prediction: Upload one pair of PDB + SDF files
   - Batch prediction: Upload multiple protein and ligand files; the system automatically matches them by filename
3. In the "Data View" tab:
   - View prediction result tables
   - Data distribution histograms and box plots
   - Download CSV results
4. In the "Heatmap Generation" tab:
   - Customize heatmap color schemes, dimensions, and color bar ranges
   - Generate protein-ligand affinity matrix heatmap
   - Download heatmap image

---

## Frequently Asked Questions

**Q: Page is blank or shows `ModuleNotFoundError` error after launch**
A: Check if the correct virtual environment is activated and confirm all pip dependencies are installed.

**Q: Pocket prediction shows `java: command not found` error**
A: P2Rank depends on Java runtime environment. Please install JDK 8 or higher.

**Q: Docking calculation is very slow**
A: Uni-Mol Docking v2 runs slowly on CPU; CUDA GPU is strongly recommended. A single docking task typically takes minutes on GPU but may require significantly longer on CPU.

**Q: Batch docking task status keeps showing `running`**
A: Check for error messages in the terminal. Common causes are missing model files or incorrect paths.

**Q: `Uni-Core` installation fails**
A: Ensure `ninja` is installed (`pip install ninja`) and PyTorch version matches your CUDA version. You may also try `pip install --no-build-isolation .`.

---

## AI Algorithms Used

| Algorithm | Purpose | Paper |
|-----------|---------|-------|
| [Uni-Mol Docking v2](https://arxiv.org/abs/2405.11769) | Molecular docking | Towards Accurate and Efficient Molecular Docking |
| [P2Rank](https://jcheminf.biomedcentral.com/articles/10.1186/s13321-018-0285-8) | Pocket prediction | P2Rank: machine learning based tool for rapid and accurate prediction of ligand binding sites |
| [PLANET](https://pubs.acs.org/doi/10.1021/acs.jcim.3c00253) | Affinity prediction | Protein-Ligand Binding Affinity Prediction |

---

## Project Structure

```
FLASH_DOCK/
├── FlashDock_0315.py              # Main program (latest version, run this directly)
├── FlashDock_web.py               # Original web program (reference only)
├── README.md
├── Batch_Docking/                 # Batch docking example input files
│   ├── receptor1~4.pdb
│   └── ligand1~4.sdf
├── Result/                        # Single run result output directory
│   ├── Binding_Affinity/
│   ├── Docking_Result/
│   ├── Predict_Pocket/
│   └── Prepare_Ligand/
├── jobs/                          # Backend task directory (auto-generated, can be cleared)
├── examples/                      # Example data
│   └── examples.zip
└── others/                        # Third-party tools and models
    ├── Uni-Mol/                   # Uni-Mol docking model
    │   └── unimol_docking_v2/
    │       ├── interface/demo.py  # Docking entry script
    │       └── *.pt              # Model weights (download required)
    ├── PLANET/                    # Affinity prediction model
    │   ├── pred.py               # Prediction entry script
    │   └── PLANET.param          # Model parameters (download required)
    ├── p2rank_2.5/                # Pocket prediction tool
    │   └── prank                  # Executable file (Java required)
    ├── Uni-Core/                  # PyTorch underlying framework
    ├── flashdock.png              # Application logo
    ├── author.png                 # Original author information
    └── author2.png                # Contributor information
```

---

## Acknowledgments

- Original project author: [小闪电-FLASH (Neo-Flash)](https://github.com/Neo-Flash/FLASH_DOCK)
- [Uni-Mol Docking v2](https://github.com/deepmodeling/Uni-Mol) - Molecular docking engine
- [P2Rank](https://github.com/rdk/p2rank) - Pocket prediction tool
- [PLANET](https://github.com/ComputArtCMCG/PLANET) - Affinity prediction model
- [Streamlit](https://streamlit.io/) - Web application framework

---

## Authors and Contributors

**Original Author**: 小闪电-FLASH (Neo-Flash)
East China University of Science and Technology (华东理工大学) School of Pharmacy | East China Normal University (华东师范大学) School of Computer Science and Technology
Email: 52265901016@stu.ecnu.edu.cn
GitHub: [Neo-Flash](https://github.com/Neo-Flash)

**Modifications and Optimization**: Nuki
Tokyo Medical and Dental University (東京医科齿科大学) (2023-2024) | Tokyo Science University (東京科学大学) (2024-2026)
Email: ma240306@tmd.ac.jp

---

## License

This project is based on modifications to [Neo-Flash/FLASH_DOCK](https://github.com/Neo-Flash/FLASH_DOCK). Please comply with the license agreement of the original project.
