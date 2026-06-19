import numpy as np

from timesfm_practice.baseline import naive_forecast, seasonal_naive_forecast
from timesfm_practice.evaluate import mae, rmse


def test_naive_forecast_repeats_last_value():
    pred = naive_forecast(np.array([1, 2, 3]), horizon=4)
    assert pred.tolist() == [3, 3, 3, 3]


def test_seasonal_naive_forecast_repeats_last_season():
    pred = seasonal_naive_forecast(np.array([1, 2, 3, 4]), horizon=5, season_length=2)
    assert pred.tolist() == [3, 4, 3, 4, 3]


def test_metrics():
    y_true = np.array([1, 2, 3])
    y_pred = np.array([1, 4, 3])
    assert mae(y_true, y_pred) == 2 / 3
    assert round(rmse(y_true, y_pred), 4) == 1.1547
