# OmniDev Environment Setup Script (PowerShell)
# This script sets up Miniconda environment and installs UV package manager

$ErrorActionPreference = "Stop"

Write-Host "🚀 Setting up OmniDev development environment..." -ForegroundColor Cyan

# Check if conda is installed
if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Conda is not installed. Please install Miniconda first:" -ForegroundColor Red
    Write-Host "   https://docs.conda.io/en/latest/miniconda.html" -ForegroundColor Yellow
    exit 1
}

# Create conda environment with Python 3.10
Write-Host "📦 Creating conda environment 'omnidev' with Python 3.10..." -ForegroundColor Cyan
conda create -n omnidev python=3.10 -y

# Activate the environment
Write-Host "🔌 Activating conda environment..." -ForegroundColor Cyan
conda activate omnidev

# Install UV package manager
Write-Host "📥 Installing UV package manager..." -ForegroundColor Cyan
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    # Install UV using PowerShell
    $uvInstallScript = "https://astral.sh/uv/install.ps1"
    Invoke-WebRequest -Uri $uvInstallScript -UseBasicParsing | Invoke-Expression
    
    # Add to PATH if needed
    $env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"
} else {
    Write-Host "✅ UV is already installed" -ForegroundColor Green
}

# Verify UV installation
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Failed to install UV. Please install manually:" -ForegroundColor Red
    Write-Host "   Visit: https://github.com/astral-sh/uv" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ UV installed successfully" -ForegroundColor Green

# Install project dependencies using UV
Write-Host "📚 Installing project dependencies with UV..." -ForegroundColor Cyan
uv pip install -e ".[dev]"

# Verify installation
Write-Host "🧪 Verifying installation..." -ForegroundColor Cyan
try {
    python -c "import omnidev; print('✅ OmniDev package imported successfully')"
} catch {
    Write-Host "❌ Failed to import OmniDev package" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ Environment setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To activate the environment in the future, run:" -ForegroundColor Yellow
Write-Host "  conda activate omnidev" -ForegroundColor White
Write-Host ""
Write-Host "To verify the installation, run:" -ForegroundColor Yellow
Write-Host "  omnidev --version" -ForegroundColor White

