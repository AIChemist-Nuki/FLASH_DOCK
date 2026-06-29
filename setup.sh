#!/bin/bash
# ============================================================
# FLASH_DOCK — one-shot install & launch
#
# Usage:
#   bash setup.sh [path/to/unimol_docking_v2_240517.pt]
#
#   bash setup.sh ~/Downloads/unimol_docking_v2_240517.pt   # place Uni-Mol weight + install + run
#   bash setup.sh                                            # install (skip weight copy) + run
#
# What it does:
#   1. checks conda/mamba + hardware (CUDA / Apple MPS / CPU)
#   2. installs the MAIN app env (requirements.txt + PyTorch + Uni-Core)
#   3. creates the ISOLATED PocketFormer env from environment-pocket.yml
#   4. fetches model weights (Uni-Mol from arg; PocketFormer from Zenodo)
#   5. prints a status summary and launches the app
# ============================================================
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; }

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

POCKET_ENV="flashdock-pocket"
POCKET_EXAMPLES="$SCRIPT_DIR/others/pocket_detection/examples"
ZENODO_WEIGHTS_URL="https://zenodo.org/records/13070037/files/best_models.tar.xz?download=1"
UNIMOL_TARGET="$SCRIPT_DIR/others/Uni-Mol/unimol_docking_v2/unimol_docking_v2_240517.pt"

echo ""
echo "========================================"
echo "  ⚡️ FLASH_DOCK  setup ⚡️"
echo "========================================"
echo ""

# ------------------------------------------------------------
# 1. environment + hardware
# ------------------------------------------------------------
info "Checking toolchain & hardware..."

if command -v mamba &>/dev/null; then SOLVER="mamba"
elif command -v conda &>/dev/null; then SOLVER="conda"
else error "conda/mamba not found. Install Miniforge: https://github.com/conda-forge/miniforge"; exit 1; fi
success "conda solver: $SOLVER"

if command -v python3 &>/dev/null; then success "Python: $(python3 --version 2>&1)"
else error "python3 not found"; exit 1; fi

ACCEL="cpu"
if command -v nvidia-smi &>/dev/null; then
    ACCEL="cuda"; success "GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1) (CUDA)"
elif [ "$(uname -s)" = "Darwin" ] && [ "$(uname -m)" = "arm64" ]; then
    ACCEL="mps"; success "Apple Silicon detected (MPS available for supported ops)"
else
    warn "No CUDA GPU; using CPU (docking will be slower)"
fi
echo ""

# ------------------------------------------------------------
# 2. MAIN app env (assumes you've activated your app env)
# ------------------------------------------------------------
if [ -z "$CONDA_DEFAULT_ENV" ] && [ -z "$VIRTUAL_ENV" ]; then
    warn "No active virtualenv/conda env detected."
    warn "Recommended:  conda create -n flash_dock python=3.9 -y && conda activate flash_dock"
    warn "Then re-run this script. Continuing may install into 'base'."
fi

info "Installing main app dependencies (requirements.txt)..."
python3 -m pip install -r requirements.txt 2>&1 | tail -3
success "App dependencies installed"

# PyTorch (platform-specific)
if ! python3 -c "import torch" 2>/dev/null; then
    info "Installing PyTorch for: $ACCEL"
    case "$ACCEL" in
        cuda) python3 -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118 2>&1 | tail -2 ;;
        mps)  python3 -m pip install torch torchvision 2>&1 | tail -2 ;;            # default wheels ship MPS on macOS
        *)    python3 -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu 2>&1 | tail -2 ;;
    esac
    success "PyTorch installed"
else
    success "PyTorch already installed"
fi

# Uni-Core (compiled against your torch)
if ! python3 -c "import unicore" 2>/dev/null; then
    info "Installing Uni-Core (may take a few minutes)..."
    python3 -m pip install ninja 2>&1 | tail -1
    ( cd "$SCRIPT_DIR/others/Uni-Core" && python3 -m pip install . 2>&1 | tail -3 )
    success "Uni-Core installed"
else
    success "Uni-Core already installed"
fi
echo ""

# ------------------------------------------------------------
# 3. PocketFormer isolated env
# ------------------------------------------------------------
if $SOLVER env list | grep -qE "^\s*${POCKET_ENV}\s|/${POCKET_ENV}$"; then
    success "PocketFormer env '${POCKET_ENV}' already exists"
else
    info "Creating PocketFormer env '${POCKET_ENV}' from environment-pocket.yml..."
    $SOLVER env create -f environment-pocket.yml
    success "PocketFormer env created"
fi

# fpocket lives inside the pocket env
if conda run -n "$POCKET_ENV" bash -c "command -v fpocket" &>/dev/null; then
    success "fpocket present in '${POCKET_ENV}'"
else
    warn "fpocket not found in '${POCKET_ENV}'. Try: $SOLVER install -n ${POCKET_ENV} -c conda-forge fpocket=4.2"
fi
echo ""

# ------------------------------------------------------------
# 4. model weights
# ------------------------------------------------------------
# Uni-Mol docking weight
if [ -n "$1" ]; then
    [ -f "$1" ] || { error "weight file not found: $1"; exit 1; }
    mkdir -p "$(dirname "$UNIMOL_TARGET")"
    cp "$1" "$UNIMOL_TARGET"
    success "Uni-Mol weight placed"
elif [ -f "$UNIMOL_TARGET" ]; then
    success "Uni-Mol weight already present"
else
    warn "Uni-Mol weight missing — docking disabled until you provide it:"
    warn "  bash setup.sh /path/to/unimol_docking_v2_240517.pt"
    warn "  download: https://github.com/deepmodeling/Uni-Mol/releases"
fi

# PocketFormer weights (Zenodo, ~396MB)
if ls "$POCKET_EXAMPLES"/fold0_best_model.pt &>/dev/null; then
    success "PocketFormer weights already present"
else
    info "Downloading PocketFormer weights from Zenodo (~396MB)..."
    if curl -fSL "$ZENODO_WEIGHTS_URL" -o "$POCKET_EXAMPLES/best_models.tar.xz"; then
        info "Extracting weights..."
        ( cd "$POCKET_EXAMPLES" && tar xJf best_models.tar.xz && rm -f best_models.tar.xz )
        success "PocketFormer weights ready"
    else
        warn "Weight download failed. Manually download best_models.tar.xz from"
        warn "https://doi.org/10.5281/zenodo.13070037 and extract into $POCKET_EXAMPLES"
    fi
fi

# PLANET affinity model
[ -f "$SCRIPT_DIR/others/PLANET/PLANET.param" ] && success "PLANET model present" \
    || warn "PLANET.param missing — affinity prediction disabled (see https://github.com/ComputArtCMCG/PLANET)"
echo ""

# ------------------------------------------------------------
# 5. work dirs
# ------------------------------------------------------------
mkdir -p jobs Result/Binding_Affinity Result/Docking_Result Result/Predict_Pocket Result/Prepare_Ligand
success "Work directories ready"

# ------------------------------------------------------------
# 6. summary
# ------------------------------------------------------------
echo ""
echo "========================================"
echo "  📋 install summary"
echo "========================================"
check() { [ "$2" = "true" ] && echo -e "  ${GREEN}✅${NC} $1" || echo -e "  ${RED}❌${NC} $1"; }

PY_OK=$(python3 -c "import streamlit, rdkit, torch, pandas" 2>/dev/null && echo true || echo false)
check "App core deps (streamlit, rdkit, torch, pandas)" "$PY_OK"
check "Uni-Core" "$(python3 -c 'import unicore' 2>/dev/null && echo true || echo false)"
check "Uni-Mol docking weight" "$([ -f "$UNIMOL_TARGET" ] && echo true || echo false)"
check "PocketFormer env ($POCKET_ENV)" "$($SOLVER env list | grep -q "$POCKET_ENV" && echo true || echo false)"
check "PocketFormer weights" "$(ls "$POCKET_EXAMPLES"/fold0_best_model.pt &>/dev/null && echo true || echo false)"
check "PLANET affinity model" "$([ -f "$SCRIPT_DIR/others/PLANET/PLANET.param" ] && echo true || echo false)"
echo "========================================"
echo ""

# ------------------------------------------------------------
# 7. launch
# ------------------------------------------------------------
if [ "$PY_OK" = "true" ]; then
    info "Launching FLASH_DOCK → http://localhost:8501  (Ctrl+C to stop)"
    echo ""
    streamlit run "$SCRIPT_DIR/app.py"
else
    error "Core dependencies missing — not launching. See errors above."
    exit 1
fi
