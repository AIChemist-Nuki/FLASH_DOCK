**🌐 Language / 言語:** [中文](README.md) | **English** | [日本語](README.ja.md)

# FLASH_DOCK ⚡️

> AI-Powered Molecular Docking Platform
>
> 🌐 Built-in multilingual UI (中文 / English / 日本語), switchable in the sidebar

FLASH_DOCK is a Streamlit web app that turns the whole workflow —
**ligand prep → pocket detection → docking → affinity scoring** — into a
ready-to-use GUI. Forked from [Neo-Flash/FLASH_DOCK](https://github.com/Neo-Flash/FLASH_DOCK) and refactored.

---

## What's new in this version (by Nuki)

| Change | Details |
|--------|---------|
| **Pocket detection → PocketFormer** | Replaces P2Rank with [PocketFormer](https://github.com/pfnet-research/pocket_detection) (graph transformer + fpocket); outputs pockets ranked by ensemble score with center coordinates. **No more Java dependency.** |
| **Modernized UI** | A cohesive "scientific instrument" design: pipeline-stage headers, monospace coordinates/scores, icon navigation, card layouts. |
| **Out-of-the-box** | New `requirements.txt` / `environment-pocket.yml`; `setup.sh` installs both envs and fetches weights automatically. |
| **Leaner code** | Removed duplicate banners and redundant imports; extracted `ui/` (theme + components) and `pocket/` (PocketFormer adapter). |
| **i18n** | 中 / en / ja, one-click switch; translations in `lang/`. |

> Roadmap: bigger & faster screening — first **Apple MPS**, then **NVIDIA CUDA**. The inference device is already configurable (CPU / MPS / CUDA); acceleration lands in a later release.

---

## Features

| # | Module | Description |
|---|--------|-------------|
| 1 | **Prepare ligand** | Upload SDF / draw (Ketcher) / SMILES → optimized 3D conformer (ETKDG + MMFF); CSV batch supported |
| 2 | **Pocket detection** | PocketFormer locates binding pockets, exports center-coordinate CSV (single + batch) |
| 3 | **Docking** | Uni-Mol Docking v2; auto-fills the grid from a pocket CSV or set it manually |
| 4 | **Batch docking** | Many proteins × many ligands, background async, UUID tracking, ZIP results |
| 5 | **Affinity** | PLANET binding-affinity prediction with data view + heatmaps |
| 6 | **Task manager** | Inspect background jobs, download results, 3D visualization |

---

## Architecture: why two environments

PocketFormer pins an older/different stack (torch + PyG + fpocket) that conflicts
with the main app (Streamlit + Uni-Mol/Uni-Core). So FLASH_DOCK runs PocketFormer
in its **own conda env**, invoked as a **subprocess** — the same pattern used for
Uni-Mol and PLANET.

| Env | Purpose | Key deps |
|-----|---------|----------|
| `flash_dock` (main) | Streamlit UI + Uni-Mol docking + PLANET | Python 3.9, torch, streamlit, rdkit, unicore |
| `flashdock-pocket` (isolated) | PocketFormer only | Python 3.10, torch<2.6, PyG 2.5.3, pytorch_scatter/cluster, fpocket 4.2 |

---

## Quick start

### Prerequisites
- **conda or mamba** ([Miniforge](https://github.com/conda-forge/miniforge) recommended)
- **Python 3.9+**
- GPU optional: NVIDIA CUDA auto-enabled; Apple Silicon uses MPS/CPU

> No Java required anymore — pocket detection uses fpocket (installed into the isolated env by `setup.sh`).

```bash
git clone https://github.com/AIChemist-Nuki/FLASH_DOCK.git
cd FLASH_DOCK
conda create -n flash_dock python=3.9 -y && conda activate flash_dock
bash setup.sh /path/to/unimol_docking_v2_240517.pt
```

`setup.sh` installs main deps + PyTorch + Uni-Core, creates the isolated
`flashdock-pocket` env (with fpocket), downloads PocketFormer weights from
Zenodo (~396MB), places the Uni-Mol weight, then launches the app at
`http://localhost:8501`.

Later runs: `conda activate flash_dock && bash setup.sh` (or `streamlit run app.py`).

---

## Model files

| Model | Size | In repo? | Use | Source |
|-------|------|----------|-----|--------|
| `unimol_docking_v2_240517.pt` | 465MB | ❌ download | Docking | [Uni-Mol Releases](https://github.com/deepmodeling/Uni-Mol/releases) |
| `fold0~4_best_model.pt` | ~396MB | ❌ download | Pocket (PocketFormer) | Zenodo [10.5281/zenodo.13070037](https://doi.org/10.5281/zenodo.13070037) (auto via `setup.sh`) |
| `PLANET.param` | 18MB | ✅ included | Affinity | — |

---

## Manual install

<details><summary>Expand</summary>

```bash
# A. main env
conda create -n flash_dock python=3.9 -y && conda activate flash_dock
pip install -r requirements.txt
pip install torch torchvision                  # pick per hardware
pip install ninja && pip install ./others/Uni-Core
# place Uni-Mol weight at others/Uni-Mol/unimol_docking_v2/unimol_docking_v2_240517.pt

# B. pocket env
conda env create -f environment-pocket.yml
# download Zenodo best_models.tar.xz, extract fold0~4_best_model.pt into
#   others/pocket_detection/examples/

# C. run
conda activate flash_dock && streamlit run app.py
```

</details>

---

## Workflow

**Prepare ligand → Pocket detection → Docking → (Batch) → Affinity.**
Grab sample files from the home page.

1. **Prepare ligand** — SDF / Ketcher / SMILES → optimized 3D SDF; CSV with `mol_name`, `smiles` for batch.
2. **Pocket detection** — upload PDB(s); single mode downloads `best_pocket.csv`, batch mode exports a CSV with `Protein File / rank / center_x/y/z` ready for batch docking. Centers come from fpocket pocket geometry, ranked by PocketFormer's ensemble score.
3. **Docking** — upload protein + ligand; a pocket CSV auto-fills the grid, or set it manually; visualize and download.
4. **Batch docking** — upload the batch pocket CSV + all proteins/ligands; edit the `Run` column; submit and note the **job ID** (runs in the background).
5. **Task manager / Affinity** — track jobs (✅/🔄/❌), download & visualize; PLANET predicts affinity and renders heatmaps.

---

## FAQ

- **fpocket / weights missing?** Create `flashdock-pocket` via `setup.sh` or `environment-pocket.yml`; ensure `fold0~4_best_model.pt` are under `others/pocket_detection/examples/`. Override the interpreter with `FLASHDOCK_POCKET_PYTHON`.
- **Docking slow?** Uni-Mol is slow on CPU — use a CUDA GPU; Apple acceleration is coming.
- **Job stuck `running`?** Check the terminal — usually a missing weight or wrong path.
- **Uni-Core build fails?** `pip install ninja` first; match torch/CUDA; try `--no-build-isolation`.

---

## AI algorithms

| Algorithm | Use | Paper / Repo |
|-----------|-----|--------------|
| [Uni-Mol Docking v2](https://arxiv.org/abs/2405.11769) | Docking | Towards Accurate and Efficient Molecular Docking |
| [PocketFormer](https://github.com/pfnet-research/pocket_detection) | Pocket detection | Ishitani et al., *Protein ligand binding site prediction using graph transformer neural network* |
| [PLANET](https://pubs.acs.org/doi/10.1021/acs.jcim.3c00253) | Affinity | Protein-Ligand Binding Affinity Prediction |

---

## Project structure

```
FLASH_DOCK/
├── app.py                    # entry: streamlit run app.py
├── requirements.txt          # main env
├── environment-pocket.yml    # isolated pocket env
├── setup.sh                  # one-shot install & launch
├── .streamlit/config.toml    # theme
├── ui/theme.py               # theme + components
├── pocket/pocketformer.py    # PocketFormer adapter
├── lang/                     # i18n (zh / en / ja)
├── Batch_Docking/ · examples/
└── others/                   # Uni-Mol · pocket_detection · PLANET · Uni-Core
```

---

## Acknowledgements

[Neo-Flash/FLASH_DOCK](https://github.com/Neo-Flash/FLASH_DOCK) · [Uni-Mol](https://github.com/deepmodeling/Uni-Mol) · [PocketFormer (Preferred Networks)](https://github.com/pfnet-research/pocket_detection) · [PLANET](https://github.com/ComputArtCMCG/PLANET) · [fpocket](https://github.com/Discngine/fpocket) · [Streamlit](https://streamlit.io/)

## Authors

**Original:** 小闪电-FLASH (Neo-Flash) · [GitHub](https://github.com/Neo-Flash)
**Refactor:** Nuki · Institute of Science Tokyo · ma240306@tmd.ac.jp

## License
Based on [Neo-Flash/FLASH_DOCK](https://github.com/Neo-Flash/FLASH_DOCK); PocketFormer is MIT. Follow each upstream project's license.
