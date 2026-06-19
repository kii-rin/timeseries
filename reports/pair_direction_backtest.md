# Pair Direction Backtest

Status: ok_web_daily_fallback
Source: web_daily_fallback
Window: 2026-06-11 through 2026-06-17
Accuracy: 33.33% across 6 checks.
Scored UP/DOWN checks: 6
Correct UP/DOWN checks: 2
Flat checks: 0

Data notes: One-week EUR/USD daily fallback backtest. Yahoo hourly report was not available in the repo, so this report uses daily EUR/USD historical rows from public web sources as a reliable fallback. The model is the same simple momentum-direction rule with lookback=3.

| Target time | Pair | Source | Guess | Actual | Result |
|---|---:|---:|---:|---:|---:|
| 2026-06-17 | EURUSD=X | web_daily_fallback | UP | DOWN | RED WRONG |
| 2026-06-16 | EURUSD=X | web_daily_fallback | UP | UP | BLUE CORRECT |
| 2026-06-15 | EURUSD=X | web_daily_fallback | UP | DOWN | RED WRONG |
| 2026-06-14 | EURUSD=X | web_daily_fallback | DOWN | UP | RED WRONG |
| 2026-06-12 | EURUSD=X | web_daily_fallback | DOWN | UP | RED WRONG |
| 2026-06-11 | EURUSD=X | web_daily_fallback | DOWN | DOWN | BLUE CORRECT |
