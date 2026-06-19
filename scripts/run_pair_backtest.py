from __future__ import annotations

import argparse
import csv
from pathlib import Path

from scripts.run_pair_direction import direction, fetch_points, guess_next


def backtest_pair(pair: str, lookback: int) -> list[dict[str, str]]:
    points = fetch_points(pair, interval="60m", range_="1mo")
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
    return rows


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


def save_markdown(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Pair Direction Backtest",
        "",
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
    parser.add_argument("--csv", default="reports/pair_direction_backtest.csv")
    parser.add_argument("--md", default="reports/pair_direction_backtest.md")
    args = parser.parse_args()

    rows = backtest_pair(args.pair, args.lookback)
    save_csv(Path(args.csv), rows)
    save_markdown(Path(args.md), rows)
    print(f"{args.pair} direction backtest accuracy: {accuracy(rows)}% across {len(rows)} checks")


if __name__ == "__main__":
    main()
