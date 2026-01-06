# Intermittent Demand Forecasting for Aircraft Parts

A comprehensive machine learning pipeline for forecasting demand of aircraft parts with intermittent demand patterns, combining time series forecasting, uncertainty quantification, and market analysis.

## Project Structure

```
Intermittant-Demand/
├── 01_data/
│   ├── raw/              # Original input data (Excel files, reports)
│   ├── processed/        # Intermediate processed data
│   └── final/            # Final output datasets
│
├── 02_notebooks/
│   ├── 01_data_preparation/      # Data cleaning & preprocessing
│   ├── 02_feature_engineering/   # Feature creation & IBA processing
│   ├── 03_modeling/              # ML model training
│   ├── 04_analysis/              # Market analysis & ensemble
│   └── extra/                    # Experimental notebooks
│
├── 03_models/
│   ├── saved_models/     # Trained model files (.pkl)
│   └── model_artifacts/  # Model metadata & mappings
│
├── 04_outputs/
│   ├── predictions/      # Model predictions by dataset
│   ├── metrics/          # Performance metrics & summaries
│   ├── visualizations/   # All plots and charts
│   └── reports/          # Text reports
│
└── 05_documentation/     # Project documentation
```

## Quick Start

### Prerequisites
- Python 3.12 (see `SETUP.md` for installation)
- Jupyter Notebook
- NVIDIA GPU (optional, for faster training)
- Required packages: See `requirements.txt` or run `pip install -r requirements.txt`

**Setup Instructions:** See `SETUP.md` for detailed environment setup.

## Step-by-Step Workflow

Follow these steps in order to run the complete pipeline:

### IBA Data Processing

**Step 1:** Run `IBA-Data.ipynb`
```bash
jupyter notebook 02_notebooks/02_feature_engineering/IBA-Data.ipynb
```

**Step 2:** Run `IBA_data_merge.ipynb`
```bash
jupyter notebook 02_notebooks/02_feature_engineering/IBA_data_merge.ipynb
```
- Output: `01_data/processed/FINAL_merged_iba_data.csv` (used in ML predictions)

### Getting ML Predictions

**Step 1:** (Optional) Run `preprocess.ipynb`
```bash
jupyter notebook 02_notebooks/01_data_preparation/preprocess.ipynb
```
- **Note:** This step is only needed if you want to generate `Aggregated_Part_Data_with_Classification.csv`. If you're using `FINAL_merged_iba_data.csv` from Step 2 above, you can skip this step.

**Step 2:** Run `ML.ipynb`
```bash
jupyter notebook 02_notebooks/03_modeling/ML.ipynb
```

### Getting Final Statistics

**Step 1:** Run `market_tightness.ipynb`
```bash
jupyter notebook 02_notebooks/02_feature_engineering/market_tightness.ipynb
```

**Step 2:** Run `combining_market_winkler.ipynb`
```bash
jupyter notebook 02_notebooks/04_analysis/combining_market_winkler.ipynb
```

**Step 3:** Run `ensamble.ipynb`
```bash
jupyter notebook 02_notebooks/04_analysis/ensamble.ipynb
```

**You're done!** Final output: `01_data/final/FINAL_streamlined_ensemble_results.csv`

---

### Detailed Workflow (Alternative View)

#### Step 1: IBA Data Processing
- **IBA-Data.ipynb**: Processes aircraft fleet data from `01_data/raw/World Fleet - October 2025.xlsx`
  - Creates family-level macro signals
  - Outputs: `01_data/processed/IBA_Family_Features_FULL.csv`
- **IBA_data_merge.ipynb**: Merges IBA features with demand data
  - Outputs: `01_data/processed/FINAL_merged_iba_data.csv` (used in ML predictions)

#### Step 2: Data Preparation (Optional)
- **preprocess.ipynb**: Loads ILS demand data from `01_data/raw/ILS-newest.xlsx`
  - Aggregates monthly data by part number
  - Classifies demand patterns (Smooth, Intermittent, Erratic, Lumpy)
  - Outputs: `01_data/processed/Aggregated_Part_Data_with_Classification.csv`
  - **Note:** Skip this if using `FINAL_merged_iba_data.csv` from Step 1

#### Step 3: Model Training
- **ML.ipynb**: Trains LightGBM and Transformer models
  - Generates quantile predictions (Q10, Q25, Q75, Q90)
  - Outputs: Predictions and metrics in `04_outputs/predictions/` and `04_outputs/metrics/`

#### Step 4: Market Analysis
- **market_tightness.ipynb**: Calculates market tightness metrics
  - Outputs: `01_data/processed/FINAL_market_tightness_enhanced_data.csv`

#### Step 5: Final Analysis & Ensemble
- **combining_market_winkler.ipynb**: Combines Winkler scores with market tightness
- **ensamble.ipynb**: Creates ensemble predictions (average of LightGBM + Transformer)
  - Outputs: `01_data/final/FINAL_streamlined_ensemble_results.csv` (final output)

## Key Outputs

### Main Final Output
- **`01_data/final/FINAL_streamlined_ensemble_results.csv`**
  - Ensemble predictions with quantiles
  - Market tightness metrics
  - Uncertainty quantification (Winkler scores)
  - Ready for production use

### Model Performance
- **Test Set Performance:**
  - MAE: 3.876 (best among all models)
  - R²: 0.700
  - 80% Prediction Interval Coverage: 83.5%

### Demand Classification
- **987 unique part numbers analyzed:**
  - Lumpy: 410 parts (41.5%) - hardest to forecast
  - Smooth: 302 parts (30.6%) - easiest to forecast
  - Erratic: 233 parts (23.6%)
  - Intermittent: 42 parts (4.3%)

## Demand Classification Methodology

Parts are classified using two metrics:

1. **ADI (Average Demand Interval)**: Average time between periods with demand
2. **CV² (Coefficient of Variation²)**: Measure of demand variability

**Classification Rules:**
- **Smooth**: ADI < 1.32 and CV² < 0.49 (predictable, consistent)
- **Intermittent**: ADI ≥ 1.32 and CV² < 0.49 (sparse but consistent)
- **Erratic**: ADI < 1.32 and CV² ≥ 0.49 (frequent but variable)
- **Lumpy**: ADI ≥ 1.32 and CV² ≥ 0.49 (sparse and highly variable)

## File Path Updates

After reorganization, update file paths in notebooks:

| Notebook | Old Path | New Path |
|----------|----------|----------|
| `preprocess.ipynb` | `ILS-newest.xlsx` | `../01_data/raw/ILS-newest.xlsx` |
| `IBA-Data.ipynb` | `World Fleet - October 2025.xlsx` | `../01_data/raw/World Fleet - October 2025.xlsx` |
| `ML.ipynb` | `FINAL_merged_iba_data.csv` | `../01_data/processed/FINAL_merged_iba_data.csv` |

## Additional Resources

- **`05_documentation/ORGANIZATION_PLAN.md`**: Detailed organization plan
- **`04_outputs/visualizations/`**: All generated plots and charts
- **`04_outputs/metrics/`**: Detailed model performance metrics

## Key Features

- Intermittent demand pattern classification
- Multiple ML models (LightGBM, Transformer)
- Ensemble predictions for improved accuracy
- Uncertainty quantification (quantile predictions)
- Market tightness analysis
- Comprehensive performance metrics

## License

**Proprietary - All Rights Reserved**

Copyright (c) 2025 Muhammad Rakeh Saleem

This project and its contents, including but not limited to:
- Source code
- Data files
- Models
- Documentation
- Any associated materials

are proprietary and confidential. 

## Contributors

- **Muhammad Rakeh Saleem** - Project creator and maintainer

