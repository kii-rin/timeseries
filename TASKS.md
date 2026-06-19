# Beginner Practice Tasks

## Level 1: Run the repo

- Install the repo with `pip install -e ".[dev]"`.
- Run `pytest`.
- Run `python scripts/run_baseline.py`.

## Level 2: Understand the data

- Open `data/raw/air_passengers.csv`.
- Find the first and last month.
- Plot `timestamp` vs `value`.
- Write down what trend and seasonality you see.

## Level 3: Baseline forecasting

- Change `--horizon` from 12 to 6.
- Compare `naive` and `seasonal_naive`.
- Explain why monthly data usually benefits from `season_length=12`.

Example:

```bash
python scripts/run_baseline.py --horizon 6 --season-length 12
```

## Level 4: Add one beginner test

Add a test that checks `train_test_split_time(df, horizon=6)` returns 138 train rows and 6 test rows.

## Level 5: Kaggle connection

- Create a Kaggle API token.
- Download `chirag19/air-passengers` with `scripts/download_kaggle.py`.
- Compare the downloaded CSV with `data/raw/air_passengers.csv`.

## Level 6: Explore a larger real dataset

Try downloading:

```bash
python scripts/download_kaggle.py --dataset talhanazir168/store-inventory-demand-forecasting-dataset --out data/kaggle/store_inventory
```

Then inspect the columns and decide which single store-item pair to forecast first.

## Level 7: TimesFM experiment

Use the same train/test split and compare TimesFM against `seasonal_naive`. Your first goal is not perfect accuracy; it is to make a clean, repeatable experiment.
