from timesfm_practice.data import load_air_passengers, train_test_split_time


def test_air_passengers_loads_real_monthly_dataset():
    df = load_air_passengers()
    assert len(df) == 144
    assert str(df["timestamp"].min().date()) == "1949-01-01"
    assert str(df["timestamp"].max().date()) == "1960-12-01"
    assert df["value"].iloc[0] == 112
    assert df["value"].iloc[-1] == 432


def test_train_test_split_keeps_time_order():
    df = load_air_passengers()
    train, test = train_test_split_time(df, horizon=12)
    assert len(train) == 132
    assert len(test) == 12
    assert train["timestamp"].max() < test["timestamp"].min()
