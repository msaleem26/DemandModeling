# Project Setup Guide

## Quick Start

### 1. Python Environment

The project uses **Python 3.12** with a virtual environment. If you need to recreate it:

```powershell
# Create virtual environment
py -3.12 -m venv venv312

# Activate
.\venv312\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. PyTorch GPU Setup

**Current Setup:**
- Python 3.12 virtual environment: `venv312/`
- PyTorch GPU: 2.5.1+cu121 (CUDA 12.1)
- GPU: NVIDIA GeForce RTX 4070

**If you need to reinstall PyTorch GPU:**

```powershell
# Activate environment first
.\venv312\Scripts\Activate.ps1

# Install PyTorch with CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 3. Jupyter Kernel

The Python 3.12 kernel is registered as "Python 3.12 (PyTorch GPU)".

To use in Jupyter:
1. Open your notebook
2. Go to: **Kernel → Change Kernel → Python 3.12 (PyTorch GPU)**

### 4. MLflow

MLflow is integrated for experiment tracking. See `MLFLOW_SETUP.md` for details.

**Quick start:**
```powershell
# Start MLflow UI
.\start_mlflow_ui.bat
# Or manually:
mlflow ui
```

Then open: `http://localhost:5000`

## Requirements

All dependencies are in `requirements.txt`. Install with:

```powershell
pip install -r requirements.txt
```

## Project Structure

```
Intermittant-Demand/
├── 01_data/           # Data files
├── 02_notebooks/      # Jupyter notebooks
├── 03_models/         # Saved models
├── 04_outputs/        # Predictions, metrics, visualizations
├── mlruns/            # MLflow experiment tracking (auto-created)
└── venv312/           # Python 3.12 virtual environment
```

## Troubleshooting

### GPU not detected
- Verify CUDA: `python -c "import torch; print(torch.cuda.is_available())"`
- Check GPU: `nvidia-smi`
- Reinstall PyTorch GPU if needed (see above)

### MLflow UI shows no experiments
- Ensure you've run the training notebook
- Check that `mlruns/` directory exists in project root
- Run `mlflow ui` from project root directory

