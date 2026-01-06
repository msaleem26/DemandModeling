# Python 3.12 Setup Script for PyTorch GPU
# 
# NOTE: This script is optional - use only if you need to recreate the virtual environment
# The environment is already set up at: venv312/
# 
# Run this after installing Python 3.12 from python.org

Write-Host "========================================"
Write-Host "Python 3.12 + PyTorch GPU Setup"
Write-Host "========================================"
Write-Host ""

# Check if Python 3.12 is available
Write-Host "Checking for Python 3.12..."
try {
    $python312 = py -3.12 --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Found: $python312"
    } else {
        throw "Python 3.12 not found"
    }
} catch {
    Write-Host "✗ Python 3.12 not found!"
    Write-Host "  Please install Python 3.12 from: https://www.python.org/downloads/release/python-31211/"
    Write-Host "  Make sure to check 'Add Python 3.12 to PATH' during installation"
    exit 1
}

# Navigate to project root
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot
Write-Host ""
Write-Host "Project directory: $projectRoot"

# Create virtual environment
Write-Host ""
Write-Host "Creating virtual environment..."
if (Test-Path "venv312") {
    Write-Host "⚠ venv312 already exists. Removing old one..."
    Remove-Item -Recurse -Force venv312
}

py -3.12 -m venv venv312
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to create virtual environment"
    exit 1
}
Write-Host "✓ Virtual environment created"

# Activate virtual environment
Write-Host ""
Write-Host "Activating virtual environment..."
& ".\venv312\Scripts\Activate.ps1"

# Upgrade pip
Write-Host ""
Write-Host "Upgrading pip..."
python -m pip install --upgrade pip --quiet

# Install PyTorch GPU
Write-Host ""
Write-Host "Installing PyTorch with CUDA 12.1 support..."
pip uninstall torch torchvision torchaudio -y --quiet
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 --quiet

# Verify PyTorch GPU
Write-Host ""
Write-Host "Verifying PyTorch GPU installation..."
$pytorchCheck = python -c "import torch; print(f'{torch.__version__},{torch.cuda.is_available()},{torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')" 2>&1
$parts = $pytorchCheck -split ','
if ($parts[1] -eq "True") {
    Write-Host "✓ PyTorch: $($parts[0])"
    Write-Host "✓ CUDA: Available"
    Write-Host "✓ GPU: $($parts[2])"
} else {
    Write-Host "⚠ PyTorch installed but CUDA not available"
    Write-Host "  Version: $($parts[0])"
}

# Install requirements
Write-Host ""
Write-Host "Installing project requirements..."
pip install -r requirements.txt --quiet

# Install Jupyter kernel
Write-Host ""
Write-Host "Setting up Jupyter kernel..."
pip install ipykernel --quiet
python -m ipykernel install --user --name=python312 --display-name="Python 3.12 (PyTorch GPU)"

Write-Host ""
Write-Host "========================================"
Write-Host "✓ Setup Complete!"
Write-Host "========================================"
Write-Host ""
Write-Host "To activate the environment, run:"
Write-Host "  .\venv312\Scripts\Activate.ps1"
Write-Host ""
Write-Host "To use in Jupyter:"
Write-Host "  1. Start Jupyter: jupyter notebook"
Write-Host "  2. Select kernel: Kernel → Change Kernel → Python 3.12 (PyTorch GPU)"
Write-Host ""

