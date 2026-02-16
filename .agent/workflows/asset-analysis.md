---
description: Standard workflow for running O2C calculations on an asset, generating charts, and organizing output
---

# Asset O2C Analysis Workflow

This workflow is used whenever the user asks to run calculations/analysis on a financial asset (e.g., NQ, ES). It performs the full pipeline: calculations, chart generation, and file organization.

## Prerequisites
- The asset must be configured in `config/assets.py` (in the `ASSETS` dictionary)
- If the asset is not configured, add it first following the existing pattern (see NQ and ES entries)

## Steps

### 1. Run O2C calculations for all 3 timeframes

Run the `o2c_periods.py` script for each timeframe (daily, weekly, monthly) for the requested asset. Replace `[ASSET]` with the asset key (e.g., NQ, ES).

```bash
# Daily
// turbo
python o2c_periods.py --asset [ASSET] --timeframe daily --output ./output/charts

# Weekly
// turbo
python o2c_periods.py --asset [ASSET] --timeframe weekly --output ./output/charts

# Monthly
// turbo
python o2c_periods.py --asset [ASSET] --timeframe monthly --output ./output/charts
```

This will automatically:
- Download price data from Yahoo Finance for 4 periods (2005-2025, 2010-2025, 2015-2025, 2020-2025)
- Calculate O2C returns (simple returns)
- Print distribution tables, statistics, and sigma bands to console
- Generate chart images (.png) with distribution tables, histograms, stats, and sigma bands

### 2. Verify chart organization

After running, verify the charts are properly organized in the expected folder structure:

```
output/charts/
└── [ASSET]/
    ├── daily/
    │   ├── DOR_O2C_D_[ASSET]_2005-2025_[DATE].png
    │   ├── DOR_O2C_D_[ASSET]_2010-2025_[DATE].png
    │   ├── DOR_O2C_D_[ASSET]_2015-2025_[DATE].png
    │   └── DOR_O2C_D_[ASSET]_2020-2025_[DATE].png
    ├── weekly/
    │   ├── DOR_O2C_W_[ASSET]_2005-2025_[DATE].png
    │   ├── DOR_O2C_W_[ASSET]_2010-2025_[DATE].png
    │   ├── DOR_O2C_W_[ASSET]_2015-2025_[DATE].png
    │   └── DOR_O2C_W_[ASSET]_2020-2025_[DATE].png
    └── monthly/
        ├── DOR_O2C_M_[ASSET]_2005-2025_[DATE].png
        ├── DOR_O2C_M_[ASSET]_2010-2025_[DATE].png
        ├── DOR_O2C_M_[ASSET]_2015-2025_[DATE].png
        └── DOR_O2C_M_[ASSET]_2020-2025_[DATE].png
```

Each asset gets 12 charts total (4 periods × 3 timeframes).

// turbo
List the output directory to confirm all 12 charts exist:
```bash
fd .png output/charts/[ASSET] --type f
```

### 3. Summary

Report to the user:
- Total charts generated (should be 12 per asset)
- Confirm folder structure is correct
- Note any errors or warnings from the calculations

## Key Details

- **Sigma bands**: ±1σ, ±1.5σ, ±2σ (no 0.5σ)
- **Return type**: Simple returns (not log returns)
- **Periods analyzed**: 2005-2025, 2010-2025, 2015-2025, 2020-2025
- **Chart naming**: `DOR_O2C_[D|W|M]_[ASSET]_[PERIOD]_[YYYYMMDD].png`
- **Output base dir**: `./output/charts`
