from __future__ import annotations

import argparse
import csv
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def fetch_points(code: str, interval: str = "60m", range_: str = "5d") -> list[dict[str, object]]:
    symbol = urllib.parse.quote(code, safe="")
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval}&range={range_}"
    req = urllib.request.Request(url, headers={"User-Agent": "timeseries-practice"})
    with urllib.request.urlopen(req, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))

    result = payload["chart"]["result"][0]
    timestamps = result["timestamp"]
    closes = result["indicators"]["quote"][0]["close"]
    rows = []
    for ts, close in zip(timestamps, closes, strict=False):
        if close is not None:
            rows.append(
                {
                    "time": datetime.fromtimestamp(ts, timezone.utc).isoformat(),
                    "close": float(close),
                }
            )
    return rows


def direction(a: float, b: float) -> str:
    if b > a:
        return "UP"
    if b < a:
        return "DOWN"
    return "FLAT"


def guess_next(rows: list[dict[str, object]], lookback: int) -> str:
    closes = [float(row["close"]) for row in rows]
    changes = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    recent = changes[-lookback:]
    score = sum(recent) / len(recent)
    if score > 0:
        return "UP"
    if score < 0:
        return "DOWN"
    return "FLAT"


def load_log(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_log(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["run_time", "pair", "from_time", "check_time", "guess", "actual", "result"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def update_old_guesses(log_rows: list[dict[str, str]], points: list[dict[str, object]]) -> None:
    close_by_time = {str(row["time"]): float(row["close"]) for row in points}
    for row in log_rows:
        if row["result"] != "WAITING":
            continue
        if row["from_time"] not in close_by_time or row["check_time"] not in close_by_time:
            continue
        actual = direction(close_by_time[row["from_time"]], close_by_time[row["check_time"]])
        row["actual"] = actual
        if actual == "FLAT":
            row["result"] = "WHITE FLAT"
        elif actual == row["guess"]:
            row["result"] = "BLUE CORRECT"
        else:
            row["result"] = "RED WRONG"


def append_new_guess(log_rows: list[dict[str, str]], points: list[dict[str, object]], pair: str, lookback: int) -> None:
    if len(points) < lookback + 2:
        raise RuntimeError("Not enough recent points to make a direction guess.")
    latest = points[-1]
    previous = points[-2]
    latest_time = str(latest["time"])
    step_seconds = (
        datetime.fromisoformat(str(latest["time"])) - datetime.fromisoformat(str(previous["time"]))
    ).total_seconds()
    check_time = (
        datetime.fromisoformat(latest_time) + __import__("datetime").timedelta(seconds=step_seconds)
    ).isoformat()

    existing = {(row["pair"], row["check_time"]) for row in log_rows}
    if (pair, check_time) in existing:
        return

    log_rows.append(
        {
            "run_time": datetime.now(timezone.utc).isoformat(),
            "pair": pair,
            "from_time": latest_time,
            "check_time": check_time,
            "guess": guess_next(points, lookback),
            "actual": "",
            "result": "WAITING",
        }
    )


def write_markdown(csv_rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Pair Direction Log",
        "",
        "Simple learning project: UP/DOWN direction guesses only. No numeric forecast output.",
        "",
        "Legend: BLUE CORRECT, RED WRONG, WHITE FLAT, WAITING.",
        "",
        "| Run time | Pair | Check time | Guess | Actual | Result |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in list(reversed(csv_rows[-50:])):
        lines.append(
            f"| {row['run_time']} | {row['pair']} | {row['check_time']} | {row['guess']} | "
            f"{row['actual'] or 'waiting'} | {row['result']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pair", default="EURUSD=X")
    parser.add_argument("--lookback", type=int, default=3)
    parser.add_argument("--csv", default="reports/pair_direction.csv")
    parser.add_argument("--md", default="reports/pair_direction.md")
    args = parser.parse_args()

    points = fetch_points(args.pair)
    rows = load_log(Path(args.csv))
    update_old_guesses(rows, points)
    append_new_guess(rows, points, args.pair, args.lookback)
    save_log(Path(args.csv), rows)
    write_markdown(rows, Path(args.md))
    print(f"Latest {args.pair} direction guess: {rows[-1]['guess']} / {rows[-1]['result']}")


if __name__ == "__main__":
    main()
