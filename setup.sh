#!/bin/bash
# ============================================================
# FLASH_DOCK — one-shot install & launch (single unified env)
#
# Usage:
#   bash setup.sh [path/to/unimol_docking_v2_240517.pt]
#
#   bash setup.sh ~/Downloads/unimol_docking_v2_240517.pt   # + place Uni-Mol weight
#   bash setup.sh                                            # install + run
#
# What it does:
#   1. checks conda/mamba + hardware (CUDA / Apple MPS / CPU)
#   2. creates ONE env `flashdock` from environment.yml (app + Pokeformer + fpocket)
#   3. best-effort installs Uni-Core (docking) into that env
#   4. fetches weights (Uni-Mol from arg; Pokeformer from Zenodo)
#   5. launches the app
# ============================================================
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; }

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

ENV_NAME="flashdock"
POCKET_EXAMPLES="$SCRIPT_DIR/others/pocket_detection/examples"
ZENODO_WEIGHTS_URL="https://zenodo.org/records/13070037/files/best_models.tar.xz?download=1"
UNIMOL_TARGET="$SCRIPT_DIR/others/Uni-Mol/unimol_docking_v2/unimol_docking_v2_240517.pt"
RUN="conda run --no-capture-output -n $ENV_NAME"

echo ""
echo "========================================"
echo "  ⚡️ FLASH_DOCK  setup ⚡️"
echo "========================================"
echo ""

# ------------------------------------------------------------
# 1. toolchain + hardware
# ------------------------------------------------------------
info "Checking toolchain & hardware..."
if command -v mamba &>/dev/null; then SOLVER="mamba"
elif command -v conda &>/dev/null; then SOLVER="conda"
else error "conda/mamba not found. Install Miniforge: https://github.com/conda-forge/miniforge"; exit 1; fi
success "conda solver: $SOLVER"

if command -v nvidia-smi &>/dev/null; then
    success "GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1) (CUDA)"
elif [ "$(uname -s)" = "Darwin" ] && [ "$(uname -m)" = "arm64" ]; then
    success "Apple Silicon detected (MPS available for supported ops)"
else
    warn "No CUDA GPU; using CPU (docking will be slower)"
fi
echo ""

# ------------------------------------------------------------
# 2. unified env
# ------------------------------------------------------------
if $SOLVER env list | grep -qE "^\s*${ENV_NAME}\s|/${ENV_NAME}$"; then
    success "Env '${ENV_NAME}' already exists"
else
    info "Creating env '${ENV_NAME}' from environment.yml (this can take a while)..."
    $SOLVER env create -y -f environment.yml
    success "Env '${ENV_NAME}' created"
fi

$RUN bash -c "command -v fpocket" &>/dev/null \
    && success "fpocket present in '${ENV_NAME}'" \
    || warn "fpocket not found in '${ENV_NAME}' — try: $SOLVER install -n ${ENV_NAME} -c conda-forge fpocket=4.2"

# best-effort: Uni-Core (needed for docking)
if $RUN python -c "import unicore" &>/dev/null; then
    success "Uni-Core present"
else
    info "Installing Uni-Core into '${ENV_NAME}' (best effort; needed for docking)..."
    $RUN pip install ninja >/dev/null 2>&1 || true
    if ( cd "$SCRIPT_DIR/others/Uni-Core" && $RUN pip install . >/dev/null 2>&1 ); then
        success "Uni-Core installed"
    else
        warn "Uni-Core install failed — docking will be unavailable until it builds. See others/Uni-Core."
    fi
fi
echo ""

# ------------------------------------------------------------
# 3. model weights
# ------------------------------------------------------------
if [ -n "$1" ]; then
    [ -f "$1" ] || { error "weight file not found: $1"; exit 1; }
    mkdir -p "$(dirname "$UNIMOL_TARGET")"; cp "$1" "$UNIMOL_TARGET"; success "Uni-Mol weight placed"
elif [ -f "$UNIMOL_TARGET" ]; then
    success "Uni-Mol weight already present"
else
    warn "Uni-Mol weight missing — docking disabled until provided:"
    warn "  bash setup.sh /path/to/unimol_docking_v2_240517.pt  (download: https://github.com/deepmodeling/Uni-Mol/releases)"
fi

if ls "$POCKET_EXAMPLES"/fold0_best_model.pt &>/dev/null; then
    success "Pokeformer weights already present"
else
    info "Downloading Pokeformer weights from Zenodo (~396MB)..."
    if curl -fSL "$ZENODO_WEIGHTS_URL" -o "$POCKET_EXAMPLES/best_models.tar.xz"; then
        ( cd "$POCKET_EXAMPLES" && tar xJf best_models.tar.xz && rm -f best_models.tar.xz )
        success "Pokeformer weights ready"
    else
        warn "Weight download failed — get best_models.tar.xz from https://doi.org/10.5281/zenodo.13070037 and extract into $POCKET_EXAMPLES"
    fi
fi

[ -f "$SCRIPT_DIR/others/PLANET/PLANET.param" ] && success "PLANET model present" \
    || warn "PLANET.param missing — affinity disabled (see https://github.com/ComputArtCMCG/PLANET)"
echo ""

# ------------------------------------------------------------
# 4. work dirs + summary
# ------------------------------------------------------------
mkdir -p jobs Result/Binding_Affinity Result/Docking_Result Result/Predict_Pocket Result/Prepare_Ligand
success "Work directories ready"

echo ""
echo "========================================"
echo "  📋 install summary"
echo "========================================"
check() { [ "$2" = "true" ] && echo -e "  ${GREEN}✅${NC} $1" || echo -e "  ${RED}❌${NC} $1"; }
APP_OK=$($RUN python -c "import streamlit, rdkit, torch, torch_geometric" 2>/dev/null && echo true || echo false)
check "App + Pokeformer core (streamlit, rdkit, torch, torch_geometric)" "$APP_OK"
check "fpocket" "$($RUN bash -c 'command -v fpocket' &>/dev/null && echo true || echo false)"
check "Uni-Core (docking)" "$($RUN python -c 'import unicore' 2>/dev/null && echo true || echo false)"
check "Uni-Mol docking weight" "$([ -f "$UNIMOL_TARGET" ] && echo true || echo false)"
check "Pokeformer weights" "$(ls "$POCKET_EXAMPLES"/fold0_best_model.pt &>/dev/null && echo true || echo false)"
check "PLANET affinity model" "$([ -f "$SCRIPT_DIR/others/PLANET/PLANET.param" ] && echo true || echo false)"
echo "========================================"
echo ""

# ------------------------------------------------------------
# 5. launch
# ------------------------------------------------------------
if [ "$APP_OK" = "true" ]; then
    info "Launching FLASH_DOCK → http://localhost:8501  (Ctrl+C to stop)"
    echo ""
    $RUN streamlit run "$SCRIPT_DIR/app.py"
else
    error "Core deps missing in '${ENV_NAME}'. Re-run, or recreate with: $SOLVER env create -f environment.yml"
    exit 1
fi
