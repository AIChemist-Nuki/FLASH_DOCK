#!/bin/bash
# ============================================================
# FLASH_DOCK 一键安装启动脚本
# 用法: bash setup.sh [模型权重文件路径]
#
# 示例:
#   bash setup.sh ~/Downloads/unimol_docking_v2_240517.pt
#   bash setup.sh   (跳过权重安装，仅安装依赖并启动)
# ============================================================

set -e

# ---------- 颜色输出 ----------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; }

# ---------- 获取脚本所在目录 ----------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "========================================"
echo "  ⚡️ FLASH_DOCK 安装与启动脚本 ⚡️"
echo "========================================"
echo ""

# ============================================================
# 1. 检查前置条件
# ============================================================
info "正在检查系统环境..."

# 检查 Python
if command -v python3 &>/dev/null; then
    PY_VERSION=$(python3 --version 2>&1)
    success "Python: $PY_VERSION"
else
    error "未找到 python3，请先安装 Python 3.8+"
    exit 1
fi

# 检查 pip
if command -v pip3 &>/dev/null || python3 -m pip --version &>/dev/null 2>&1; then
    success "pip: 可用"
else
    error "未找到 pip，请先安装 pip"
    exit 1
fi

# 检查 Java
if command -v java &>/dev/null; then
    JAVA_VERSION=$(java -version 2>&1 | head -1)
    success "Java: $JAVA_VERSION"
else
    warn "未找到 Java。口袋预测(P2Rank)功能将不可用。"
    warn "安装方法: sudo apt install default-jdk (Ubuntu) / brew install openjdk (macOS)"
fi

# 检查 CUDA
if command -v nvidia-smi &>/dev/null; then
    GPU_INFO=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
    success "GPU: $GPU_INFO (将使用 CUDA 加速)"
    HAS_CUDA=true
else
    warn "未检测到 CUDA GPU，将使用 CPU 模式（对接速度会较慢）"
    HAS_CUDA=false
fi

echo ""

# ============================================================
# 2. 处理模型权重文件
# ============================================================
MODEL_TARGET="$SCRIPT_DIR/others/Uni-Mol/unimol_docking_v2/unimol_docking_v2_240517.pt"

if [ -n "$1" ]; then
    MODEL_SRC="$1"
    info "正在处理模型权重文件..."

    if [ ! -f "$MODEL_SRC" ]; then
        error "文件不存在: $MODEL_SRC"
        exit 1
    fi

    # 检查文件名
    BASENAME=$(basename "$MODEL_SRC")
    if [[ "$BASENAME" != *".pt" ]]; then
        warn "文件 $BASENAME 不是 .pt 格式，请确认是否为正确的模型文件"
    fi

    # 创建目标目录
    mkdir -p "$(dirname "$MODEL_TARGET")"

    # 复制或移动模型文件
    if [ "$(realpath "$MODEL_SRC")" != "$(realpath "$MODEL_TARGET" 2>/dev/null)" ]; then
        info "正在复制模型权重到项目目录..."
        cp "$MODEL_SRC" "$MODEL_TARGET"
        success "模型权重已放置到: others/Uni-Mol/unimol_docking_v2/"
    else
        success "模型权重已在正确位置"
    fi
else
    if [ -f "$MODEL_TARGET" ]; then
        success "模型权重已存在: others/Uni-Mol/unimol_docking_v2/unimol_docking_v2_240517.pt"
    else
        warn "未提供模型权重文件路径，分子对接功能将不可用"
        warn "用法: bash setup.sh /path/to/unimol_docking_v2_240517.pt"
        warn "下载地址: https://github.com/deepmodeling/Uni-Mol/releases"
    fi
fi

echo ""

# ============================================================
# 3. 安装 Python 依赖
# ============================================================
info "正在安装 Python 依赖..."

# 检查是否在虚拟环境中
if [ -n "$VIRTUAL_ENV" ] || [ -n "$CONDA_DEFAULT_ENV" ]; then
    success "检测到虚拟环境: ${VIRTUAL_ENV:-$CONDA_DEFAULT_ENV}"
    PIP_EXTRA=""
else
    warn "未检测到虚拟环境，建议使用 conda 或 venv"
    warn "例如: conda create -n flashdock python=3.9 && conda activate flashdock"
    PIP_EXTRA="--break-system-packages"
fi

# 安装 PyTorch（如果未安装）
python3 -c "import torch" 2>/dev/null
if [ $? -ne 0 ]; then
    info "正在安装 PyTorch..."
    if [ "$HAS_CUDA" = true ]; then
        pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu118 $PIP_EXTRA 2>&1 | tail -3
    else
        pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cpu $PIP_EXTRA 2>&1 | tail -3
    fi
    success "PyTorch 安装完成"
else
    success "PyTorch 已安装"
fi

# 安装 Uni-Core（如果未安装）
python3 -c "import unicore" 2>/dev/null
if [ $? -ne 0 ]; then
    info "正在安装 Uni-Core（可能需要几分钟）..."
    pip3 install ninja $PIP_EXTRA 2>&1 | tail -1
    cd "$SCRIPT_DIR/others/Uni-Core"
    pip3 install . $PIP_EXTRA 2>&1 | tail -3
    cd "$SCRIPT_DIR"
    success "Uni-Core 安装完成"
else
    success "Uni-Core 已安装"
fi

# 安装其他依赖
info "正在安装应用依赖..."
pip3 install \
    streamlit \
    streamlit-molstar \
    streamlit-ketcher \
    py3Dmol \
    stmol \
    rdkit-pypi \
    pandas \
    numpy \
    scipy \
    scikit-learn \
    matplotlib \
    seaborn \
    tqdm \
    lmdb \
    sh \
    biopandas \
    $PIP_EXTRA 2>&1 | tail -5

success "所有 Python 依赖安装完成"
echo ""

# ============================================================
# 4. 检查 P2Rank 权限
# ============================================================
PRANK="$SCRIPT_DIR/others/p2rank_2.5/prank"
if [ -f "$PRANK" ]; then
    chmod +x "$PRANK"
    success "P2Rank 可执行权限已设置"
else
    warn "P2Rank 未找到，口袋预测功能将不可用"
    warn "请下载: https://github.com/rdk/p2rank/releases/download/2.5/p2rank_2.5.tar.gz"
fi

# ============================================================
# 5. 检查 PLANET 模型
# ============================================================
if [ -f "$SCRIPT_DIR/others/PLANET/PLANET.param" ]; then
    success "PLANET 亲和力预测模型已就位"
else
    warn "PLANET 模型参数缺失，亲和力预测功能将不可用"
    warn "请从 https://github.com/ComputArtCMCG/PLANET 获取 PLANET.param"
fi

echo ""

# ============================================================
# 6. 创建必要目录
# ============================================================
mkdir -p jobs Result/Binding_Affinity Result/Docking_Result Result/Predict_Pocket Result/Prepare_Ligand
success "工作目录已创建"

# ============================================================
# 7. 最终检查
# ============================================================
echo ""
echo "========================================"
echo "  📋 安装状态总结"
echo "========================================"

check_item() {
    if [ "$2" = "true" ]; then
        echo -e "  ${GREEN}✅${NC} $1"
    else
        echo -e "  ${RED}❌${NC} $1"
    fi
}

# Python 依赖
PY_OK=$(python3 -c "import streamlit, rdkit, torch, pandas; print('true')" 2>/dev/null || echo "false")
check_item "Python 核心依赖 (streamlit, rdkit, torch, pandas)" "$PY_OK"

# Uni-Core
UC_OK=$(python3 -c "import unicore; print('true')" 2>/dev/null || echo "false")
check_item "Uni-Core 框架" "$UC_OK"

# 模型权重
[ -f "$MODEL_TARGET" ] && MW_OK="true" || MW_OK="false"
check_item "Uni-Mol 对接模型权重 (465MB)" "$MW_OK"

# P2Rank
[ -x "$PRANK" ] && PR_OK="true" || PR_OK="false"
check_item "P2Rank 口袋预测工具" "$PR_OK"

# PLANET
[ -f "$SCRIPT_DIR/others/PLANET/PLANET.param" ] && PL_OK="true" || PL_OK="false"
check_item "PLANET 亲和力预测模型" "$PL_OK"

# Java
command -v java &>/dev/null && JV_OK="true" || JV_OK="false"
check_item "Java 运行环境 (口袋预测需要)" "$JV_OK"

echo "========================================"
echo ""

# ============================================================
# 8. 启动应用
# ============================================================
if [ "$PY_OK" = "true" ]; then
    info "正在启动 FLASH_DOCK..."
    echo ""
    echo "  🌐 应用地址: http://localhost:8501"
    echo "  📌 按 Ctrl+C 停止服务"
    echo ""
    streamlit run "$SCRIPT_DIR/FlashDock_0315.py"
else
    error "核心依赖缺失，无法启动。请检查上方错误信息。"
    exit 1
fi
