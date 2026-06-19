from __future__ import annotations

import argparse
import csv
import json
import urllib.request
from datetime import date, timedelta
from pathlib import Path

from scripts.run_pair_direction import direction, fetch_points, guess_next


def fetch_daily_frankfurter(base: str = "EUR", quote: str = "USD", days: int = 90) -> list[dict[str, object]]:
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=days)
    url = f"https://api.frankfurter.app/{start.isoformat()}..{end.isoformat()}?from={base}&to={quote}"
    req = urllib.request.Request(url, headers={"User-Agent": "timeseries-practice"})
    with urllib.request.urlopen(req, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    rows = []
    for day, rates in sorted(payload.get("rates", {}).items()):
        if quote in rates:
            rows.append({"time": day, "close": float(rates[quote])})
    return rows


def points_from_source(pair: str, window: str) -> tuple[list[dict[str, object]], str]:
    try:
        points = fetch_points(pair, interval="60m", range_=window)
        if len(points) >= 10:
            return points, f"yahoo_hourly_{window}"
    except Exception:
        pass

    if pair == "EURUSD=X":
        points = fetch_daily_frankfurter("EUR", "USD", days=90)
        return points, "frankfurter_daily_90d"

    return [], "no_fallback_for_pair"


def backtest_pair(pair: str, lookback: int, window: str) -> tuple[list[dict[str, str]], str]:
    points, source = points_from_source(pair, window)
    if len(points) < lookback + 3:
        return [], f"not_enough_points_from_{source}: got {len(points)}, need at least {lookback + 3}"

    rows: list[dict[str, str]] = []
    for idx in range(lookback + 1, len(points) - 1):
        history = points[: idx + 1]
        from_point = points[idx]
        target_point = points[idx + 1]
        guess = guess_next(history, lookback)
        actual = direction(float(from_point["close"]), float(target_point["close"]))
        if actual == "FLAT":
            result = "WHITE FLAT"
        elif actual == guess:
            result = "BLUE CORRECT"
        else:
            result = "RED WRONG"
        rows.append(
            {
                "target_time": str(target_point["time"]),
                "pair": pair,
                "source": source,
                "guess": guess,
                "actual": actual,
                "result": result,
            }
        )
    return rows, f"ok_{source}"


def accuracy(rows: list[dict[str, str]]) -> float:
    scored = [row for row in rows if row["actual"] != "FLAT"]
    if not scored:
        return 0.0
    correct = sum(1 for row in scored if row["result"] == "BLUE CORRECT")
    return round(100 * correct / len(scored), 2)


def save_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["target_time", "pair", "source", "guess", "actual", "result"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def save_markdown(path: Path, rows: list[dict[str, str]], status: str, window: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    source = rows[0]["source"] if rows else "none"
    lines = [
        "# Pair Direction Backtest",
        "",
        f"Status: {status}",
        f"Source: {source}",
        f"Requested Yahoo window: {window}",
        f"Accuracy: {accuracy(rows)}% across {len(rows)} checks.",
        "",
        "| Target time | Pair | Source | Guess | Actual | Result |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in list(reversed(rows[-72:])):
        lines.append(
            f"| {row['target_time']} | {row['pair']} | {row['source']} | "
            f"{row['guess']} | {row['actual']} | {row['result']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pair", default="EURUSD=X")
    parser.add_argument("--lookback", type=int, default=3)
    parser.add_argument("--window", default="7d", help="Yahoo chart range, e.g. 7d, 5d, or 1mo")
    parser.add_argument("--csv", default="reports/pair_direction_backtest.csv")
    parser.add_argument("--md", default="reports/pair_direction_backtest.md")
    args = parser.parse_args()

    rows, status = backtest_pair(args.pair, args.lookback, args.window)
    save_csv(Path(args.csv), rows)
    save_markdown(Path(args.md), rows, status, args.window)
    print(f"{args.pair} direction backtest status={status} accuracy={accuracy(rows)}% checks={len(rows)}")


if __name__ == "__main__":
    main()
