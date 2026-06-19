from scripts.run_weather_russell import guess_next_temp, temp_direction


def test_temperature_direction_labels():
    assert temp_direction(70.0, 71.0) == "WARMER"
    assert temp_direction(71.0, 70.0) == "COOLER"
    assert temp_direction(70.0, 70.0) == "SAME"


def test_guess_next_temp_smoke():
    rows = [
        {"time": "a", "temperature_f": 70.0},
        {"time": "b", "temperature_f": 71.0},
        {"time": "c", "temperature_f": 72.0},
        {"time": "d", "temperature_f": 73.0},
    ]
    assert guess_next_temp(rows, 3) == "WARMER"
