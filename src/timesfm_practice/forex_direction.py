from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class DirectionResult:
    previous_close: float
    latest_close: float
    actual_direction: str
    predicted_direction: str
    status: str


def direction_from_change(previous_value: float, current_value: float) -> str:
    """Return UP, DOWN, or FLAT for a two-point move."""
    if current_value > previous_value:
        return "UP"
    if current_value < previous_value:
        return "DOWN"
    return "FLAT"


def momentum_direction(closes: pd.Series, lookback: int = 3) -> str:
    """Beginner direction model: follow recent average momentum.

    This is intentionally simple for learning. It is not trading advice.
    """
    if lookback <= 0:
        raise ValueError("lookback must be positive")
    clean = pd.Series(closes, dtype="float64").dropna()
    if len(clean) < lookback + 1:
        raise ValueError("not enough close values for the requested lookback")
    recent_changes = clean.diff().dropna().tail(lookback)
    score = float(recent_changes.mean())
    if score > 0:
        return "UP"
    if score < 0:
        return "DOWN"
    return "FLAT"


def score_direction_guess(previous_close: float, actual_close: float, predicted_direction: str) -> DirectionResult:
    """Compare one UP/DOWN guess with the actual next move."""
    actual_direction = direction_from_change(previous_close, actual_close)
    if actual_direction == "FLAT":
        status = "⚪ FLAT"
    elif actual_direction == predicted_direction:
        status = "🔵 CORRECT"
    else:
        status = "🔴 WRONG"
    return DirectionResult(
        previous_close=previous_close,
        latest_close=actual_close,
        actual_direction=actual_direction,
        predicted_direction=predicted_direction,
        status=status,
    )
