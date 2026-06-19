# Pair Direction Backtest

Status: awaiting_yahoo_hourly_7d_run
Source: yahoo_hourly_7d
Window: last 7 days, hourly candles

This report is configured for the requested hourly 7-day backtest. The previous daily fallback report was removed because it was not what was requested.

Run target:

```bash
python scripts/run_pair_backtest.py --pair EURUSD=X --window 7d
```

Expected output after the workflow completes:

- hourly EUR/USD checks for the last 7 days
- UP/DOWN/FLAT actual direction
- BLUE CORRECT / RED WRONG / WHITE FLAT result
- accuracy across hourly checks
