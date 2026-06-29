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
| **Pocket detection → Pokeformer** | Replaces P2Rank with [Pokeformer](https://github.com/pfnet-research/pocket_detection) (graph transformer + fpocket); outputs pockets ranked by ensemble score with center coordinates. **No more Java dependency.** |
| **Modernized UI** | A cohesive "scientific instrument" design: pipeline-stage headers, monospace coordinates/scores, icon navigation, card layouts. |
| **Out-of-the-box · one env** | New `environment.yml`; `setup.sh` creates **one** conda env (app + Pokeformer) and fetches weights automatically. |
| **Leaner code** | Removed duplicate banners and redundant imports; extracted `ui/` (theme + components) and `pocket/` (Pokeformer adapter). |
| **i18n** | 中 / en / ja, one-click switch; translations in `lang/`. |

> Roadmap: bigger & faster screening — first **Apple MPS**, then **NVIDIA CUDA**. The inference device is already configurable (CPU / MPS / CUDA); acceleration lands in a later release.

---

## Features

| # | Module | Description |
|---|--------|-------------|
| 1 | **Prepare ligand** | Upload SDF / draw (Ketcher) / SMILES → optimized 3D conformer (ETKDG + MMFF); CSV batch supported |
| 2 | **Pocket detection** | Pokeformer locates binding pockets, exports center-coordinate CSV (single + batch) |
| 3 | **Docking** | Uni-Mol Docking v2; auto-fills the grid from a pocket CSV or set it manually |
| 4 | **Batch docking** | Many proteins × many ligands, background async, UUID tracking, ZIP results |
| 5 | **Affinity** | PLANET binding-affinity prediction with data view + heatmaps |
| 6 | **Task manager** | Inspect background jobs, download results, 3D visualization |

---

## Architecture: one environment for everything

The whole project uses a **single conda env `flashdock`** (Python 3.10) shared by
the UI and Pokeformer pocket detection. Pokeformer is still invoked as a
**subprocess** (like Uni-Mol and PLANET) for isolation and future acceleration.

Key deps (all from `environment.yml`): `torch 2.5.x`, `PyG 2.5.3`,
`pytorch_scatter/cluster`, `fpocket 4.2`, `rdkit`, `streamlit`.

> Why torch 2.5.x: Pokeformer needs `pytorch_scatter/cluster`, which on Apple
> Silicon only come from conda-forge and only pair cleanly with `torch<2.6`
> (2.5.x also keeps `torch.load`'s safe default and ships MPS) — the newest
> version that satisfies both the app and Pokeformer in one env.

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
bash setup.sh /path/to/unimol_docking_v2_240517.pt
```

`setup.sh` creates the single `flashdock` env from `environment.yml` (app +
Pokeformer + fpocket), best-effort installs Uni-Core (docking), downloads
Pokeformer weights from Zenodo (~396MB), places the Uni-Mol weight, then launches
the app at `http://localhost:8501`.

Later runs: `conda activate flashdock && streamlit run app.py`.

---

## Model files

| Model | Size | In repo? | Use | Source |
|-------|------|----------|-----|--------|
| `unimol_docking_v2_240517.pt` | 465MB | ❌ download | Docking | [Uni-Mol Releases](https://github.com/deepmodeling/Uni-Mol/releases) |
| `fold0~4_best_model.pt` | ~396MB | ❌ download | Pocket (Pokeformer) | Zenodo [10.5281/zenodo.13070037](https://doi.org/10.5281/zenodo.13070037) (auto via `setup.sh`) |
| `PLANET.param` | 18MB | ✅ included | Affinity | — |

---

## Manual install

<details><summary>Expand</summary>

```bash
# 1. single env (torch / PyG / scatter+cluster / fpocket / rdkit / streamlit)
conda env create -f environment.yml && conda activate flashdock

# 2. docking needs Uni-Core (affinity needs DGL) — install as needed
pip install ninja && pip install ./others/Uni-Core

# 3. weights
#  - Uni-Mol -> others/Uni-Mol/unimol_docking_v2/unimol_docking_v2_240517.pt
#  - Pokeformer: download Zenodo best_models.tar.xz, extract fold0~4_best_model.pt
#    into others/pocket_detection/examples/

# 4. run
streamlit run app.py
```

</details>

---

## Workflow

**Prepare ligand → Pocket detection → Docking → (Batch) → Affinity.**
Grab sample files from the home page.

1. **Prepare ligand** — SDF / Ketcher / SMILES → optimized 3D SDF; CSV with `mol_name`, `smiles` for batch.
2. **Pocket detection** — upload PDB(s); single mode downloads `best_pocket.csv`, batch mode exports a CSV with `Protein File / rank / center_x/y/z` ready for batch docking. Centers come from fpocket pocket geometry, ranked by Pokeformer's ensemble score.
3. **Docking** — upload protein + ligand; a pocket CSV auto-fills the grid, or set it manually; visualize and download.
4. **Batch docking** — upload the batch pocket CSV + all proteins/ligands; edit the `Run` column; submit and note the **job ID** (runs in the background).
5. **Task manager / Affinity** — track jobs (✅/🔄/❌), download & visualize; PLANET predicts affinity and renders heatmaps.

---

## FAQ

- **fpocket / weights missing?** Create `flashdock` via `setup.sh` or `environment.yml`; ensure `fold0~4_best_model.pt` are under `others/pocket_detection/examples/`. To run Pokeformer from a different env, set `FLASHDOCK_POCKET_PYTHON`.
- **Docking slow?** Uni-Mol is slow on CPU — use a CUDA GPU; Apple acceleration is coming.
- **Job stuck `running`?** Check the terminal — usually a missing weight or wrong path.
- **Uni-Core build fails?** `pip install ninja` first; match torch/CUDA; try `--no-build-isolation`.

---

## AI algorithms

| Algorithm | Use | Paper / Repo |
|-----------|-----|--------------|
| [Uni-Mol Docking v2](https://arxiv.org/abs/2405.11769) | Docking | Towards Accurate and Efficient Molecular Docking |
| [Pokeformer](https://github.com/pfnet-research/pocket_detection) | Pocket detection | Ishitani et al., *Protein ligand binding site prediction using graph transformer neural network* |
| [PLANET](https://pubs.acs.org/doi/10.1021/acs.jcim.3c00253) | Affinity | Protein-Ligand Binding Affinity Prediction |

---

## Project structure

```
FLASH_DOCK/
├── app.py                    # entry: streamlit run app.py
├── environment.yml           # single conda env (app + Pokeformer)
├── requirements.txt          # pip layer (reference)
├── setup.sh                  # one-shot install & launch
├── .streamlit/config.toml    # theme
├── ui/theme.py               # theme + components
├── pocket/pokeformer.py    # Pokeformer adapter
├── lang/                     # i18n (zh / en / ja)
├── Batch_Docking/ · examples/
└── others/                   # Uni-Mol · pocket_detection · PLANET · Uni-Core
```

---

## Acknowledgements

[Neo-Flash/FLASH_DOCK](https://github.com/Neo-Flash/FLASH_DOCK) · [Uni-Mol](https://github.com/deepmodeling/Uni-Mol) · [Pokeformer (Preferred Networks)](https://github.com/pfnet-research/pocket_detection) · [PLANET](https://github.com/ComputArtCMCG/PLANET) · [fpocket](https://github.com/Discngine/fpocket) · [Streamlit](https://streamlit.io/)

## Authors

**Original:** 小闪电-FLASH (Neo-Flash) · [GitHub](https://github.com/Neo-Flash)
**Refactor:** Nuki · Institute of Science Tokyo · ma240306@tmd.ac.jp

## License
Based on [Neo-Flash/FLASH_DOCK](https://github.com/Neo-Flash/FLASH_DOCK); Pokeformer is MIT. Follow each upstream project's license.
