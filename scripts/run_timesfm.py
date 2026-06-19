from __future__ import annotations

import argparse

from timesfm_practice.data import load_air_passengers, train_test_split_time
from timesfm_practice.evaluate import mae, rmse
from timesfm_practice.timesfm_runner import forecast_with_timesfm


def main() -> None:
    parser = argparse.ArgumentParser(description="Run TimesFM on the real AirPassengers dataset.")
    parser.add_argument("--csv", default="data/raw/air_passengers.csv")
    parser.add_argument("--horizon", type=int, default=12)
    args = parser.parse_args()

    df = load_air_passengers(args.csv)
    train, test = train_test_split_time(df, horizon=args.horizon)

    point, quantiles = forecast_with_timesfm(train["value"].to_numpy(), horizon=args.horizon)
    y_test = test["value"].to_numpy()

    print("Point forecast shape:", point.shape)
    print("Quantile forecast shape:", quantiles.shape)
    print(f"TimesFM MAE={mae(y_test, point):.2f} RMSE={rmse(y_test, point):.2f}")
    print("First 5 point forecasts:", point[:5])


if __name__ == "__main__":
    main()
