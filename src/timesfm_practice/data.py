from __future__ import annotations

from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = {"month", "passengers"}


def load_air_passengers(path: str | Path = "data/raw/air_passengers.csv") -> pd.DataFrame:
    """Load the real AirPassengers monthly time series.

    The bundled sample is the classic monthly international airline passengers
    dataset, also mirrored on Kaggle. Passenger values are in thousands.
    """
    df = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["month"], format="%Y-%m")
    df["value"] = pd.to_numeric(df["passengers"], errors="raise")
    return df[["timestamp", "value", "month", "passengers"]]


def train_test_split_time(df: pd.DataFrame, horizon: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split a time series without shuffling."""
    if horizon <= 0:
        raise ValueError("horizon must be positive")
    if len(df) <= horizon:
        raise ValueError("horizon must be smaller than the dataset length")
    return df.iloc[:-horizon].copy(), df.iloc[-horizon:].copy()
