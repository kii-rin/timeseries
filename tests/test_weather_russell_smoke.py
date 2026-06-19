from scripts.run_weather_russell import mean_absolute_error, predict_value


def test_predict_value_uses_daily_and_recent_pattern():
    rows = []
    for i in range(30):
        rows.append(
            {
                "time": str(i),
                "temperature_f": 70.0 + i,
                "humidity_pct": 50.0,
                "wind_speed_mph": 10.0,
                "cloud_cover_pct": 20.0,
                "pressure_hpa": 1000.0,
                "precip_probability_pct": 0.0,
            }
        )
    assert isinstance(predict_value(rows, "temperature_f", 3), float)


def test_mean_absolute_error_smoke():
    rows = [
        {"absolute_error_temperature_f": "1.0"},
        {"absolute_error_temperature_f": "3.0"},
    ]
    assert mean_absolute_error(rows, "temperature_f") == 2.0
