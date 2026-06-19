from __future__ import annotations

import numpy as np


def naive_forecast(history: np.ndarray, horizon: int) -> np.ndarray:
    """Repeat the last observed value for every future step."""
    history = np.asarray(history, dtype=float)
    if history.size == 0:
        raise ValueError("history must contain at least one value")
    if horizon <= 0:
        raise ValueError("horizon must be positive")
    return np.repeat(history[-1], horizon)


def seasonal_naive_forecast(history: np.ndarray, horizon: int, season_length: int = 12) -> np.ndarray:
    """Repeat the latest full seasonal window.

    For monthly data, use season_length=12.
    """
    history = np.asarray(history, dtype=float)
    if horizon <= 0:
        raise ValueError("horizon must be positive")
    if season_length <= 0:
        raise ValueError("season_length must be positive")
    if history.size < season_length:
        raise ValueError("history must be at least as long as season_length")
    pattern = history[-season_length:]
    repeats = int(np.ceil(horizon / season_length))
    return np.tile(pattern, repeats)[:horizon]
