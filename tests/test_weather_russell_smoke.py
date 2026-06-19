from scripts.run_weather_russell import mean_absolute_error, naive_temperature_prediction


def test_naive_temperature_prediction_smoke():
    rows = [
        {"time": "a", "temperature_f": 70.0},
        {"time": "b", "temperature_f": 71.0},
        {"time": "c", "temperature_f": 72.0},
        {"time": "d", "temperature_f": 73.0},
    ]
    assert naive_temperature_prediction(rows, 3) == 74.0


def test_mean_absolute_error_smoke():
    rows = [
        {"absolute_error_f": "1.0"},
        {"absolute_error_f": "3.0"},
    ]
    assert mean_absolute_error(rows) == 2.0
