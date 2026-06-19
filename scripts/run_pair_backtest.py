from __future__ import annotations

import argparse
import csv
from pathlib import Path

from scripts.run_pair_direction import direction, fetch_points, guess_next


def backtest_pair(pair: str, lookback: int, window: str) -> tuple[list[dict[str, str]], str]:
    """Backtest pair direction guesses.

    Yahoo's hourly endpoint can be inconsistent for long windows, so this script
    defaults to a shorter supported window and writes an error report instead of
    silently failing.
    """
    try:
        points = fetch_points(pair, interval="60m", range_=window)
    except Exception as exc:  # noqa: BLE001
        return [], f"data_fetch_failed: {type(exc).__name__}: {exc}"

    if len(points) < lookback + 3:
        return [], f"not_enough_points: got {len(points)}, need at least {lookback + 3}"

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
                "guess": guess,
                "actual": actual,
                "result": result,
            }
        )
    return rows, "ok"


def accuracy(rows: list[dict[str, str]]) -> float:
    scored = [row for row in rows if row["actual"] != "FLAT"]
    if not scored:
        return 0.0
    correct = sum(1 for row in scored if row["result"] == "BLUE CORRECT")
    return round(100 * correct / len(scored), 2)


def save_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["target_time", "pair", "guess", "actual", "result"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def save_markdown(path: Path, rows: list[dict[str, str]], status: str, window: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Pair Direction Backtest",
        "",
        f"Status: {status}",
        f"Window: {window}",
        f"Accuracy: {accuracy(rows)}% across {len(rows)} hourly checks.",
        "",
        "| Target hour | Pair | Guess | Actual | Result |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in list(reversed(rows[-72:])):
        lines.append(f"| {row['target_time']} | {row['pair']} | {row['guess']} | {row['actual']} | {row['result']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pair", default="EURUSD=X")
    parser.add_argument("--lookback", type=int, default=3)
    parser.add_argument("--window", default="5d", help="Yahoo chart range, e.g. 5d or 1mo")
    parser.add_argument("--csv", default="reports/pair_direction_backtest.csv")
    parser.add_argument("--md", default="reports/pair_direction_backtest.md")
    args = parser.parse_args()

    rows, status = backtest_pair(args.pair, args.lookback, args.window)
    save_csv(Path(args.csv), rows)
    save_markdown(Path(args.md), rows, status, args.window)
    print(f"{args.pair} direction backtest status={status} accuracy={accuracy(rows)}% checks={len(rows)}")


if __name__ == "__main__":
    main()
