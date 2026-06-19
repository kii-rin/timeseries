# TimesFM Practice Repo

A beginner-friendly repo for practicing time-series forecasting workflows inspired by Google Research's TimesFM project.

This version avoids synthetic data. It includes a tiny real dataset so you can run tests immediately, plus an optional Kaggle downloader for exploring more datasets.

## Dataset included

`data/raw/air_passengers.csv` contains the classic **AirPassengers** monthly international airline passenger totals from 1949 to 1960. Values are in thousands.

Kaggle mirrors of this dataset include `chirag19/air-passengers`, and the original dataset is also available in R's built-in `datasets` package.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e ".[dev]"
```

## Run the beginner baseline

```bash
python scripts/run_baseline.py
```

Expected output includes MAE and RMSE for:

- `naive`: repeats the last known value
- `seasonal_naive`: repeats the same month from the previous year

## Run tests

```bash
pytest
```

The tests check:

- the real CSV loads correctly
- the split keeps time order
- baseline forecasts behave as expected
- evaluation metrics are correct

## Optional: connect to Kaggle

Install the Kaggle client:

```bash
pip install kaggle
```

Create a Kaggle token from your Kaggle account settings, then place it here:

```bash
~/.kaggle/kaggle.json
```

Download the AirPassengers Kaggle mirror:

```bash
python scripts/download_kaggle.py --dataset chirag19/air-passengers --out data/kaggle
```

Try another beginner time-series dataset:

```bash
python scripts/download_kaggle.py --dataset talhanazir168/store-inventory-demand-forecasting-dataset --out data/kaggle/store_inventory
```

## Where TimesFM fits

Start with the baseline first. Once you understand the input format, open `scripts/run_timesfm.py` and adapt it to the same `timestamp,value` columns.

The goal is to learn the workflow:

1. Load a real time series.
2. Split the last horizon as test data.
3. Run a simple baseline.
4. Measure error.
5. Compare TimesFM against the baseline.
