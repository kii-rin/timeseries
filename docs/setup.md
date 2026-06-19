# Hourly Direction Setup

This repo now has a small scheduled direction-guessing workflow.

## What runs every hour

GitHub Actions runs:

```bash
python scripts/run_pair_direction.py --pair EURUSD=X
```

The workflow file is:

```text
.github/workflows/hourly-pair-direction.yml
```

It wakes up every hour, runs the script, commits the updated report files, then stops.

## Output files

The job writes:

```text
reports/pair_direction.csv
reports/pair_direction.md
```

The log is direction-only. It does not output a predicted number.

Possible guess values:

- `UP`
- `DOWN`
- `FLAT`

Possible result values:

- `BLUE CORRECT`
- `RED WRONG`
- `WHITE FLAT`
- `WAITING`

## Smoke test

Run:

```bash
pytest tests/test_pair_direction_smoke.py
```

This checks the direction labels and the tiny beginner momentum guess.

## TimesFM original repo output

The original TimesFM example returns two objects:

```python
point_forecast, quantile_forecast = model.forecast(...)
```

The point forecast is the main central forecast. The quantile forecast is the richer output and can be used like a confidence or uncertainty band.

For this beginner hourly project, the current workflow keeps things simpler: it only records direction, actual direction, and whether the guess was correct.

## How to run manually

In GitHub:

1. Open the repo.
2. Go to **Actions**.
3. Pick **hourly-pair-direction**.
4. Click **Run workflow**.

In Codespaces:

```bash
python scripts/run_pair_direction.py --pair EURUSD=X
pytest
```
