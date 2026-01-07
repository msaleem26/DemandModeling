# MLflow Integration Guide

## Overview

MLflow has been integrated into the Transformer model training pipeline for experiment tracking, model versioning, and hyperparameter optimization.

## Setup

### 1. Install MLflow

```bash
pip install mlflow
```

Or install all requirements:
```bash
pip install -r requirements.txt mmmmm
```

### 2. MLflow Tracking

MLflow is configured to use **local file-based tracking** by default. All experiments are stored in the `mlruns/` directory (created automatically).

## Usage

### Main Transformer Training

When you run the main Transformer training cell (Cell 53), MLflow will:

1. **Create/Get Experiment**: `Transformer_Demand_Forecasting`
2. **Start a Run**: Named based on demand pattern (e.g., `transformer_baseline_Intermittent`)
3. **Log Hyperparameters**: All model architecture and training parameters
4. **Log Metrics**: 
   - Training and validation loss per epoch
   - Best validation loss
   - Final validation metrics (MAE, RMSE, WAPE, R², etc.)
   - Final test metrics
5. **Log Model**: PyTorch model saved to MLflow
6. **Log Artifacts**: Part number mapping JSON

### Hyperparameter Sweep

When you run the hyperparameter sweep cell (Cell 54), MLflow will:

1. **Create/Get Experiment**: `Transformer_Hyperparameter_Sweep`
2. **Create Nested Runs**: One run per configuration tested
3. **Log Each Configuration**:
   - Hyperparameters for that config
   - Validation MAE
   - Tag indicating if it's the best config
4. **Log Best Model**: The best performing model is saved
5. **Create Summary Run**: Summary of best configuration

## Viewing Results

### Start MLflow UI

**Important**: Always run MLflow UI from the **project root directory** (where `mlruns/` is located).

**Option 1: Use the helper script**
- Windows: Double-click `start_mlflow_ui.bat` or run it from command line
- Linux/Mac: Run `./start_mlflow_ui.sh` (make it executable first: `chmod +x start_mlflow_ui.sh`)

**Option 2: Manual start**
From the project root directory:

```bash
cd C:\Users\msaleem\Work\Intermittant-Demand
mlflow ui
```

This will start a web server (usually at `http://localhost:5000`) where you can:

- **View Experiments**: See all experiments and runs
- **Compare Runs**: Compare metrics across different runs
- **View Parameters**: See hyperparameters for each run
- **Download Models**: Download logged models
- **View Artifacts**: Access logged files and models

### Accessing via Browser

1. Open your browser
2. Navigate to `http://localhost:5000`
3. Select an experiment from the left sidebar
4. Click on individual runs to see details

## MLflow Features Used

### 1. Experiment Tracking
- **Experiments**: Separate experiments for baseline training and hyperparameter sweeps
- **Runs**: Individual training runs with unique names
- **Nested Runs**: Hyperparameter sweep uses nested runs for organization

### 2. Parameter Logging
- Model architecture parameters (d_model, nhead, num_layers, etc.)
- Training hyperparameters (learning rate, batch size, epochs)
- Data configuration (sequence length, horizon, demand pattern)

### 3. Metric Logging
- Per-epoch metrics (train_loss, val_loss)
- Final evaluation metrics (MAE, RMSE, WAPE, R², MASE, etc.)
- Best validation loss

### 4. Model Versioning
- PyTorch models saved with MLflow
- Model artifacts (part number mappings)
- Best models from hyperparameter sweeps

### 5. Tags
- `best_config`: Indicates if a hyperparameter config is the best
- `sweep_summary`: Marks summary runs

## File Structure

```
Intermittant-Demand/
├── mlruns/                    # MLflow tracking data (auto-created)
│   ├── 0/                     # Experiment metadata
│   ├── 1/                     # Experiment runs
│   └── ...
├── requirements.txt           # Includes mlflow>=2.0.0
└── MLFLOW_SETUP.md           # This file
```

## Advanced Usage

### Remote Tracking Server

To use a remote MLflow tracking server instead of local files:

```python
# In the notebook, before mlflow.set_experiment()
mlflow.set_tracking_uri("http://your-mlflow-server:5000")
```

### Querying Results Programmatically

```python
import mlflow

# Get experiment
experiment = mlflow.get_experiment_by_name("Transformer_Demand_Forecasting")

# Search runs
runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])
print(runs[['metrics.val_mae', 'params.d_model', 'params.nhead']])

# Get best run
best_run = runs.loc[runs['metrics.val_mae'].idxmin()]
print(f"Best run: {best_run['run_id']}")
print(f"Best val_mae: {best_run['metrics.val_mae']}")
```

### Loading a Logged Model

```python
import mlflow.pytorch

# Load model from a specific run
run_id = "your-run-id"
model = mlflow.pytorch.load_model(f"runs:/{run_id}/transformer_model")
```

## Benefits

1. **Reproducibility**: All hyperparameters and metrics are logged
2. **Comparison**: Easy comparison of different model configurations
3. **Model Management**: Versioned models with metadata
4. **Collaboration**: Share experiments with team members
5. **Analysis**: Query and analyze results programmatically

## Troubleshooting

### MLflow UI shows no experiments
**Most common issue**: The `mlruns/` directory doesn't exist or is in the wrong location.

**Solution**:
1. **Check if mlruns exists**: Look in your project root directory (`C:\Users\msaleem\Work\Intermittant-Demand\mlruns`)
2. **Verify you ran the training**: Make sure you executed the Transformer training cell (Cell 53)
3. **Check the tracking URI**: When you run the training cell, it should print:
   ```
   ✓ MLflow tracking URI: file:///C:/Users/msaleem/Work/Intermittant-Demand/mlruns
     mlruns directory: C:\Users\msaleem\Work\Intermittant-Demand\mlruns
   ```
4. **Run MLflow UI from project root**: Always run `mlflow ui` from the project root, not from the notebook directory

### MLflow UI not starting
- Check if port 5000 is already in use
- Try: `mlflow ui --port 5001`
- Make sure you're in the project root directory when running `mlflow ui`

### Experiments not showing
- Ensure you've run the training cells
- Check that `mlruns/` directory exists
- Verify MLflow tracking URI is set correctly

### Models not loading
- Ensure the run_id is correct
- Check that the model was logged successfully
- Verify PyTorch version compatibility

## Next Steps

1. Run your training cells - MLflow will automatically track everything
2. Start MLflow UI: `mlflow ui`
3. Explore your experiments in the web interface
4. Compare different runs to find the best configuration
5. Use the logged models for inference or further analysis

