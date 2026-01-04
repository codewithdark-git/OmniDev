#!/bin/bash
# OmniDev Environment Setup Script
# This script sets up Miniconda environment and installs UV package manager

set -e

echo "🚀 Setting up OmniDev development environment..."

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo "❌ Conda is not installed. Please install Miniconda first:"
    echo "   https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

# Create conda environment with Python 3.10
echo "📦 Creating conda environment 'omnidev' with Python 3.10..."
conda create -n omnidev python=3.10 -y

# Activate the environment
echo "🔌 Activating conda environment..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate omnidev

# Install UV package manager
echo "📥 Installing UV package manager..."
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
else
    echo "✅ UV is already installed"
fi

# Verify UV installation
if ! command -v uv &> /dev/null; then
    echo "❌ Failed to install UV. Please install manually:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✅ UV installed successfully"

# Install project dependencies using UV
echo "📚 Installing project dependencies with UV..."
uv pip install -e ".[dev]"

# Verify installation
echo "🧪 Verifying installation..."
python -c "import omnidev; print('✅ OmniDev package imported successfully')" || {
    echo "❌ Failed to import OmniDev package"
    exit 1
}

echo ""
echo "✅ Environment setup complete!"
echo ""
echo "To activate the environment in the future, run:"
echo "  conda activate omnidev"
echo ""
echo "To verify the installation, run:"
echo "  omnidev --version"

