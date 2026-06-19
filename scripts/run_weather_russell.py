from __future__ import annotations

import argparse
import csv
import json
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

RUSSELL_LAT = 38.8953
RUSSELL_LON = -98.8598
PLACE = "Russell, Kansas"


def fetch_forecast(latitude: float = RUSSELL_LAT, longitude: float = RUSSELL_LON) -> list[dict[str, object]]:
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
    return _fetch_open_meteo("https://api.open-meteo.com/v1/forecast", params)


def fetch_archive(start: date, end: date, latitude: float = RUSSELL_LAT, longitude: float = RUSSELL_LON) -> list[dict[str, object]]:
    params = urllib.parse.urlencode(
        {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "hourly": "temperature_2m,precipitation_probability",
            "temperature_unit": "fahrenheit",
            "timezone": "UTC",
        }
    )
    return _fetch_open_meteo("https://archive-api.open-meteo.com/v1/archive", params)


def _fetch_open_meteo(base_url: str, params: str) -> list[dict[str, object]]:
    req = urllib.request.Request(f"{base_url}?{params}", headers={"User-Agent": "timeseries-practice"})
    with urllib.request.urlopen(req, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))

    rows = []
    hourly = payload.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    precip = hourly.get("precipitation_probability", [None] * len(times))
    for t, temp, rain_chance in zip(times, temps, precip, strict=False):
        if temp is None:
            continue
        rows.append(
            {
                "time": datetime.fromisoformat(t).replace(tzinfo=timezone.utc).isoformat(),
                "temperature_f": round(float(temp), 1),
                "precip_probability": "" if rain_chance is None else int(rain_chance),
            }
        )
    return rows


def naive_temperature_prediction(history: list[dict[str, object]], lookback: int = 3) -> float:
    """Predict next hour's temperature as the recent average change added to latest temp."""
    if len(history) < lookback + 1:
        raise ValueError("not enough rows for prediction")
    temps = [float(row["temperature_f"]) for row in history]
    changes = [temps[i] - temps[i - 1] for i in range(1, len(temps))]
    avg_change = sum(changes[-lookback:]) / lookback
    return round(temps[-1] + avg_change, 1)


def load_log(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_log(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "run_time",
        "place",
        "from_time",
        "target_time",
        "predicted_temp_f",
        "actual_temp_f",
        "absolute_error_f",
        "precip_probability",
        "status",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def update_pending(rows: list[dict[str, str]], observed: list[dict[str, object]]) -> None:
    temp_by_time = {str(row["time"]): float(row["temperature_f"]) for row in observed}
    for row in rows:
        if row.get("status") != "WAITING":
            continue
        target_time = row["target_time"]
        if target_time not in temp_by_time:
            continue
        actual = round(temp_by_time[target_time], 1)
        predicted = float(row["predicted_temp_f"])
        error = round(abs(actual - predicted), 1)
        row["actual_temp_f"] = str(actual)
        row["absolute_error_f"] = str(error)
        row["status"] = "DONE"


def append_next_prediction(rows: list[dict[str, str]], weather_rows: list[dict[str, object]], lookback: int) -> None:
    now = datetime.now(timezone.utc)
    past_or_now = [row for row in weather_rows if datetime.fromisoformat(str(row["time"])) <= now]
    if len(past_or_now) < lookback + 1:
        past_or_now = weather_rows[: lookback + 1]
    latest = past_or_now[-1]
    latest_time = str(latest["time"])
    target_time = (datetime.fromisoformat(latest_time) + timedelta(hours=1)).isoformat()
    if (PLACE, target_time) in {(row["place"], row["target_time"]) for row in rows}:
        return

    rows.append(
        {
            "run_time": now.isoformat(),
            "place": PLACE,
            "from_time": latest_time,
            "target_time": target_time,
            "predicted_temp_f": str(naive_temperature_prediction(past_or_now, lookback)),
            "actual_temp_f": "",
            "absolute_error_f": "",
            "precip_probability": str(latest.get("precip_probability", "")),
            "status": "WAITING",
        }
    )


def backtest(rows: list[dict[str, object]], lookback: int) -> list[dict[str, str]]:
    output = []
    for idx in range(lookback, len(rows) - 1):
        history = rows[: idx + 1]
        target = rows[idx + 1]
        pred = naive_temperature_prediction(history, lookback)
        actual = round(float(target["temperature_f"]), 1)
        output.append(
            {
                "target_time": str(target["time"]),
                "predicted_temp_f": str(pred),
                "actual_temp_f": str(actual),
                "absolute_error_f": str(round(abs(actual - pred), 1)),
            }
        )
    return output


def write_backtest_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["target_time", "predicted_temp_f", "actual_temp_f", "absolute_error_f"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def mean_absolute_error(rows: list[dict[str, str]]) -> float:
    if not rows:
        return 0.0
    return round(sum(float(row["absolute_error_f"]) for row in rows) / len(rows), 2)


def write_markdown(rows: list[dict[str, str]], backtest_rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    completed = [row for row in rows if row.get("status") == "DONE" and row.get("absolute_error_f")]
    lines = [
        "# Russell, Kansas Hourly Temperature Log",
        "",
        "Hourly beginner forecast for next-hour temperature in degrees Fahrenheit.",
        "",
        f"Live completed MAE: {mean_absolute_error(completed)} °F across {len(completed)} checked predictions.",
        f"Backtest MAE: {mean_absolute_error(backtest_rows)} °F across {len(backtest_rows)} hourly predictions.",
        "",
        "| Run time | Target hour | Predicted °F | Actual °F | Error °F | Status |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in list(reversed(rows[-72:])):
        lines.append(
            f"| {row['run_time']} | {row['target_time']} | {row['predicted_temp_f']} | "
            f"{row['actual_temp_f'] or 'waiting'} | {row['absolute_error_f'] or 'waiting'} | {row['status']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lookback", type=int, default=3)
    parser.add_argument("--csv", default="reports/weather_russell.csv")
    parser.add_argument("--md", default="reports/weather_russell.md")
    parser.add_argument("--backtest-csv", default="reports/weather_russell_backtest.csv")
    args = parser.parse_args()

    today = datetime.now(timezone.utc).date()
    month_start = today.replace(day=1)
    archive_end = today - timedelta(days=1)
    archive_rows = fetch_archive(month_start, archive_end) if archive_end >= month_start else []
    forecast_rows = fetch_forecast()
    observed_rows = archive_rows + forecast_rows

    log_rows = load_log(Path(args.csv))
    update_pending(log_rows, observed_rows)
    append_next_prediction(log_rows, forecast_rows, args.lookback)
    backtest_rows = backtest(archive_rows, args.lookback)

    save_log(Path(args.csv), log_rows)
    write_backtest_csv(Path(args.backtest_csv), backtest_rows)
    write_markdown(log_rows, backtest_rows, Path(args.md))
    latest = log_rows[-1]
    print(
        f"Russell next-hour temp prediction: {latest['predicted_temp_f']} °F "
        f"for {latest['target_time']} / {latest['status']}"
    )
    print(f"Backtest MAE since {month_start}: {mean_absolute_error(backtest_rows)} °F")


if __name__ == "__main__":
    main()
