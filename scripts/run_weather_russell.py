from __future__ import annotations

import argparse
import csv
import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

RUSSELL_LAT = 38.8953
RUSSELL_LON = -98.8598


def fetch_hourly_weather(latitude: float = RUSSELL_LAT, longitude: float = RUSSELL_LON) -> list[dict[str, object]]:
    params = urllib.parse.urlencode(
        {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "temperature_2m,precipitation_probability",
            "temperature_unit": "fahrenheit",
            "timezone": "UTC",
            "forecast_days": 3,
        }
    )
    url = f"https://api.open-meteo.com/v1/forecast?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "timeseries-practice"})
    with urllib.request.urlopen(req, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))

    rows = []
    for t, temp, rain_chance in zip(
        payload["hourly"]["time"],
        payload["hourly"]["temperature_2m"],
        payload["hourly"]["precipitation_probability"],
        strict=False,
    ):
        rows.append(
            {
                "time": datetime.fromisoformat(t).replace(tzinfo=timezone.utc).isoformat(),
                "temperature_f": float(temp),
                "precip_probability": int(rain_chance),
            }
        )
    return rows


def temp_direction(a: float, b: float) -> str:
    if b > a:
        return "WARMER"
    if b < a:
        return "COOLER"
    return "SAME"


def guess_next_temp(rows: list[dict[str, object]], lookback: int) -> str:
    temps = [float(row["temperature_f"]) for row in rows]
    changes = [temps[i] - temps[i - 1] for i in range(1, len(temps))]
    recent = changes[-lookback:]
    score = sum(recent) / len(recent)
    if score > 0:
        return "WARMER"
    if score < 0:
        return "COOLER"
    return "SAME"


def confidence(rows: list[dict[str, object]], guess: str, lookback: int) -> str:
    temps = [float(row["temperature_f"]) for row in rows]
    recent_dirs = [temp_direction(temps[i - 1], temps[i]) for i in range(1, len(temps))][-lookback:]
    if not recent_dirs:
        return "0%"
    return f"{round(100 * sum(1 for item in recent_dirs if item == guess) / len(recent_dirs))}%"


def load_log(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_log(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["run_time", "place", "from_time", "check_time", "guess", "confidence", "actual", "result"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def update_old_guesses(log_rows: list[dict[str, str]], weather_rows: list[dict[str, object]]) -> None:
    temp_by_time = {str(row["time"]): float(row["temperature_f"]) for row in weather_rows}
    for row in log_rows:
        if row["result"] != "WAITING":
            continue
        if row["from_time"] not in temp_by_time or row["check_time"] not in temp_by_time:
            continue
        actual = temp_direction(temp_by_time[row["from_time"]], temp_by_time[row["check_time"]])
        row["actual"] = actual
        if actual == "SAME":
            row["result"] = "WHITE SAME"
        elif actual == row["guess"]:
            row["result"] = "BLUE CORRECT"
        else:
            row["result"] = "RED WRONG"


def append_new_guess(log_rows: list[dict[str, str]], weather_rows: list[dict[str, object]], lookback: int) -> None:
    now = datetime.now(timezone.utc)
    past_or_now = [row for row in weather_rows if datetime.fromisoformat(str(row["time"])) <= now]
    if len(past_or_now) < lookback + 2:
        past_or_now = weather_rows[: lookback + 2]
    latest = past_or_now[-1]
    latest_time = str(latest["time"])
    check_time = (datetime.fromisoformat(latest_time) + timedelta(hours=1)).isoformat()

    existing = {(row["place"], row["check_time"]) for row in log_rows}
    if ("Russell, Kansas", check_time) in existing:
        return

    guess = guess_next_temp(past_or_now, lookback)
    log_rows.append(
        {
            "run_time": now.isoformat(),
            "place": "Russell, Kansas",
            "from_time": latest_time,
            "check_time": check_time,
            "guess": guess,
            "confidence": confidence(past_or_now, guess, lookback),
            "actual": "",
            "result": "WAITING",
        }
    )


def write_markdown(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Russell, Kansas Weather Direction Log",
        "",
        "Hourly beginner weather direction guesses for the next hour's temperature move.",
        "",
        "Legend: BLUE CORRECT, RED WRONG, WHITE SAME, WAITING.",
        "",
        "| Run time | Place | Check time | Guess | Confidence | Actual | Result |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in list(reversed(rows[-50:])):
        lines.append(
            f"| {row['run_time']} | {row['place']} | {row['check_time']} | {row['guess']} | "
            f"{row['confidence']} | {row['actual'] or 'waiting'} | {row['result']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lookback", type=int, default=3)
    parser.add_argument("--csv", default="reports/weather_russell.csv")
    parser.add_argument("--md", default="reports/weather_russell.md")
    args = parser.parse_args()

    weather_rows = fetch_hourly_weather()
    rows = load_log(Path(args.csv))
    update_old_guesses(rows, weather_rows)
    append_new_guess(rows, weather_rows, args.lookback)
    save_log(Path(args.csv), rows)
    write_markdown(rows, Path(args.md))
    print(f"Russell weather next-hour guess: {rows[-1]['guess']} confidence={rows[-1]['confidence']} / {rows[-1]['result']}")


if __name__ == "__main__":
    main()
