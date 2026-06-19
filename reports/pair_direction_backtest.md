# Pair Direction Backtest

Status: ok_web_daily_fallback
Source: web_daily_fallback
Window: 2026-05-15 through 2026-06-17
Accuracy: 42.11% across 20 checks.
Scored UP/DOWN checks: 19
Correct UP/DOWN checks: 8
Flat checks: 1

Data notes: Yahoo hourly report was not available in the repo, so this report uses daily EUR/USD historical rows from public web sources as a reliable fallback. The model is the same simple momentum-direction rule with lookback=3.

| Target time | Pair | Source | Guess | Actual | Result |
|---|---:|---:|---:|---:|---:|
| 2026-06-17 | EURUSD=X | web_daily_fallback | UP | DOWN | RED WRONG |
| 2026-06-16 | EURUSD=X | web_daily_fallback | UP | UP | BLUE CORRECT |
| 2026-06-15 | EURUSD=X | web_daily_fallback | UP | DOWN | RED WRONG |
| 2026-06-14 | EURUSD=X | web_daily_fallback | DOWN | UP | RED WRONG |
| 2026-06-12 | EURUSD=X | web_daily_fallback | DOWN | UP | RED WRONG |
| 2026-06-11 | EURUSD=X | web_daily_fallback | DOWN | DOWN | BLUE CORRECT |
| 2026-06-10 | EURUSD=X | web_daily_fallback | DOWN | DOWN | BLUE CORRECT |
| 2026-06-09 | EURUSD=X | web_daily_fallback | DOWN | UP | RED WRONG |
| 2026-06-08 | EURUSD=X | web_daily_fallback | UP | DOWN | RED WRONG |
| 2026-06-05 | EURUSD=X | web_daily_fallback | DOWN | FLAT | WHITE FLAT |
| 2026-06-04 | EURUSD=X | web_daily_fallback | DOWN | UP | RED WRONG |
| 2026-06-03 | EURUSD=X | web_daily_fallback | UP | DOWN | RED WRONG |
| 2026-06-02 | EURUSD=X | web_daily_fallback | UP | UP | BLUE CORRECT |
| 2026-06-01 | EURUSD=X | web_daily_fallback | UP | UP | BLUE CORRECT |
| 2026-05-29 | EURUSD=X | web_daily_fallback | DOWN | UP | RED WRONG |
| 2026-05-28 | EURUSD=X | web_daily_fallback | UP | DOWN | RED WRONG |
| 2026-05-27 | EURUSD=X | web_daily_fallback | UP | UP | BLUE CORRECT |
| 2026-05-26 | EURUSD=X | web_daily_fallback | UP | DOWN | RED WRONG |
| 2026-05-25 | EURUSD=X | web_daily_fallback | DOWN | UP | RED WRONG |
| 2026-05-22 | EURUSD=X | web_daily_fallback | DOWN | DOWN | BLUE CORRECT |
