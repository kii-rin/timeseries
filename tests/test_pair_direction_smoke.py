from scripts.run_pair_direction import direction, guess_next


def test_direction_smoke():
    assert direction(1.0, 2.0) == "UP"
    assert direction(2.0, 1.0) == "DOWN"
    assert direction(1.0, 1.0) == "FLAT"


def test_guess_next_smoke():
    rows = [
        {"time": "a", "close": 1.0},
        {"time": "b", "close": 1.1},
        {"time": "c", "close": 1.2},
        {"time": "d", "close": 1.3},
    ]
    assert guess_next(rows, 3) == "UP"
