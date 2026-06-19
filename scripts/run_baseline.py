from __future__ import annotations

import argparse

from timesfm_practice.baseline import naive_forecast, seasonal_naive_forecast
from timesfm_practice.data import load_air_passengers, train_test_split_time
from timesfm_practice.evaluate import mae, rmse


def main() -> None:
    parser = argparse.ArgumentParser(description="Run beginner baselines on a real time-series CSV.")
    parser.add_argument("--csv", default="data/raw/air_passengers.csv")
    parser.add_argument("--horizon", type=int, default=12)
    parser.add_argument("--season-length", type=int, default=12)
    args = parser.parse_args()

    df = load_air_passengers(args.csv)
    train, test = train_test_split_time(df, horizon=args.horizon)

    y_train = train["value"].to_numpy()
    y_test = test["value"].to_numpy()

    forecasts = {
        "naive": naive_forecast(y_train, args.horizon),
        "seasonal_naive": seasonal_naive_forecast(y_train, args.horizon, args.season_length),
    }

    print(f"Dataset rows: {len(df)} | train: {len(train)} | test: {len(test)}")
    for name, pred in forecasts.items():
        print(f"{name:15s} MAE={mae(y_test, pred):8.2f} RMSE={rmse(y_test, pred):8.2f}")


if __name__ == "__main__":
    main()
