# Hourly Backtesting Reports

This project now keeps two hourly experiments.

## Russell, Kansas weather

Workflow:

```text
.github/workflows/hourly-russell-weather.yml
```

Runs every hour at minute 17.

Outputs:

```text
reports/weather_russell.csv
reports/weather_russell.md
reports/weather_russell_backtest.csv
```

The weather model predicts a numeric next-hour temperature in degrees Fahrenheit.

Columns include:

- `predicted_temp_f`
- `actual_temp_f`
- `absolute_error_f`
- `status`

Performance metric:

```text
MAE = average absolute error in degrees Fahrenheit
```

The backtest uses hourly historical weather from the beginning of the current month through yesterday.

## Pair direction

Workflow:

```text
.github/workflows/hourly-pair-direction.yml
```

Runs every hour at minute 7.

Outputs:

```text
reports/pair_direction.csv
reports/pair_direction.md
reports/pair_direction_backtest.csv
reports/pair_direction_backtest.md
```

The pair model predicts only direction:

- `UP`
- `DOWN`
- `FLAT`

Performance metric:

```text
accuracy = correct UP/DOWN guesses / scored UP/DOWN hours
```

## Manual commands

```bash
python scripts/run_weather_russell.py
python scripts/run_pair_direction.py --pair EURUSD=X
python scripts/run_pair_backtest.py --pair EURUSD=X
pytest
```

## How to compare

Weather gives numeric error in degrees Fahrenheit. Lower MAE is better.

Pair direction gives accuracy percentage. Higher accuracy is better.

These are not the same metric, so compare them as separate learning experiments rather than one directly beating the other.
