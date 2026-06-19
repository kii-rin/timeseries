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
HOURLY_FIELDS = [
    "temperature_2m",
    "relative_humidity_2m",
    "wind_speed_10m",
    "cloud_cover",
    "surface_pressure",
    "precipitation_probability",
]
TARGETS = {
    "temperature_f": "°F",
    "humidity_pct": "%",
    "wind_speed_mph": "mph",
    "cloud_cover_pct": "%",
    "pressure_hpa": "hPa",
    "precip_probability_pct": "%",
}


def fetch_forecast(latitude: float = RUSSELL_LAT, longitude: float = RUSSELL_LON) -> list[dict[str, object]]:
    params = urllib.parse.urlencode(
        {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": ",".join(HOURLY_FIELDS),
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
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
            "hourly": ",".join(HOURLY_FIELDS),
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "timezone": "UTC",
        }
    )
    return _fetch_open_meteo("https://archive-api.open-meteo.com/v1/archive", params)


def _fetch_open_meteo(base_url: str, params: str) -> list[dict[str, object]]:
    req = urllib.request.Request(f"{base_url}?{params}", headers={"User-Agent": "timeseries-practice"})
    with urllib.request.urlopen(req, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))

    hourly = payload.get("hourly", {})
    times = hourly.get("time", [])
    rows = []
    for i, t in enumerate(times):
        timestamp = datetime.fromisoformat(t).replace(tzinfo=timezone.utc)
        row = {
            "time": timestamp.isoformat(),
            "hour_utc": timestamp.hour,
            "day_of_week": timestamp.weekday(),
            "temperature_f": _num(hourly.get("temperature_2m", [None] * len(times))[i]),
            "humidity_pct": _num(hourly.get("relative_humidity_2m", [None] * len(times))[i]),
            "wind_speed_mph": _num(hourly.get("wind_speed_10m", [None] * len(times))[i]),
            "cloud_cover_pct": _num(hourly.get("cloud_cover", [None] * len(times))[i]),
            "pressure_hpa": _num(hourly.get("surface_pressure", [None] * len(times))[i]),
            "precip_probability_pct": _num(hourly.get("precipitation_probability", [None] * len(times))[i]),
        }
        if row["temperature_f"] is not None:
            rows.append(row)
    return rows


def _num(value: object) -> float | None:
    if value is None:
        return None
    return round(float(value), 1)


def predict_value(history: list[dict[str, object]], target: str, lookback: int = 3) -> float:
    """Predict the next hour using recent movement and same-hour-yesterday seasonality."""
    clean = [row for row in history if row.get(target) is not None]
    if len(clean) < lookback + 1:
        raise ValueError(f"not enough rows for {target}")
    values = [float(row[target]) for row in clean]
    changes = [values[i] - values[i - 1] for i in range(1, len(values))]
    momentum_prediction = values[-1] + sum(changes[-lookback:]) / lookback

    if len(clean) >= 24:
        daily_prediction = float(clean[-24][target])
        prediction = 0.55 * daily_prediction + 0.45 * momentum_prediction
    else:
        prediction = momentum_prediction

    if target in {"humidity_pct", "cloud_cover_pct", "precip_probability_pct"}:
        prediction = max(0.0, min(100.0, prediction))
    if target == "wind_speed_mph":
        prediction = max(0.0, prediction)
    return round(prediction, 1)


def predict_all(history: list[dict[str, object]], lookback: int) -> dict[str, float]:
    return {target: predict_value(history, target, lookback) for target in TARGETS}


def load_log(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def live_fieldnames() -> list[str]:
    base = ["run_time", "place", "from_time", "target_time", "hour_utc", "day_of_week", "status"]
    for target in TARGETS:
        base.extend([f"predicted_{target}", f"actual_{target}", f"absolute_error_{target}"])
    return base


def save_log(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=live_fieldnames())
        writer.writeheader()
        writer.writerows(rows)


def update_pending(rows: list[dict[str, str]], observed: list[dict[str, object]]) -> None:
    by_time = {str(row["time"]): row for row in observed}
    for row in rows:
        if row.get("status") != "WAITING":
            continue
        actual_row = by_time.get(row["target_time"])
        if not actual_row:
            continue
        for target in TARGETS:
            actual = actual_row.get(target)
            if actual is None:
                continue
            predicted = float(row[f"predicted_{target}"])
            row[f"actual_{target}"] = str(round(float(actual), 1))
            row[f"absolute_error_{target}"] = str(round(abs(float(actual) - predicted), 1))
        row["status"] = "DONE"


def append_next_prediction(rows: list[dict[str, str]], weather_rows: list[dict[str, object]], lookback: int) -> None:
    now = datetime.now(timezone.utc)
    past_or_now = [row for row in weather_rows if datetime.fromisoformat(str(row["time"])) <= now]
    if len(past_or_now) < lookback + 1:
        past_or_now = weather_rows[: lookback + 1]
    latest = past_or_now[-1]
    latest_time = str(latest["time"])
    target_dt = datetime.fromisoformat(latest_time) + timedelta(hours=1)
    target_time = target_dt.isoformat()
    if (PLACE, target_time) in {(row["place"], row["target_time"]) for row in rows}:
        return

    preds = predict_all(past_or_now, lookback)
    new_row = {
        "run_time": now.isoformat(),
        "place": PLACE,
        "from_time": latest_time,
        "target_time": target_time,
        "hour_utc": str(target_dt.hour),
        "day_of_week": str(target_dt.weekday()),
        "status": "WAITING",
    }
    for target, pred in preds.items():
        new_row[f"predicted_{target}"] = str(pred)
        new_row[f"actual_{target}"] = ""
        new_row[f"absolute_error_{target}"] = ""
    rows.append(new_row)


def backtest(rows: list[dict[str, object]], lookback: int) -> list[dict[str, str]]:
    output = []
    for idx in range(max(24, lookback), len(rows) - 1):
        history = rows[: idx + 1]
        target_row = rows[idx + 1]
        preds = predict_all(history, lookback)
        result = {
            "target_time": str(target_row["time"]),
            "hour_utc": str(target_row["hour_utc"]),
            "day_of_week": str(target_row["day_of_week"]),
        }
        for target, pred in preds.items():
            actual = target_row.get(target)
            result[f"predicted_{target}"] = str(pred)
            result[f"actual_{target}"] = "" if actual is None else str(round(float(actual), 1))
            result[f"absolute_error_{target}"] = "" if actual is None else str(round(abs(float(actual) - pred), 1))
        output.append(result)
    return output


def backtest_fieldnames() -> list[str]:
    base = ["target_time", "hour_utc", "day_of_week"]
    for target in TARGETS:
        base.extend([f"predicted_{target}", f"actual_{target}", f"absolute_error_{target}"])
    return base


def write_backtest_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=backtest_fieldnames())
        writer.writeheader()
        writer.writerows(rows)


def mean_absolute_error(rows: list[dict[str, str]], target: str) -> float:
    errors = [float(row[f"absolute_error_{target}"]) for row in rows if row.get(f"absolute_error_{target}") not in {None, ""}]
    if not errors:
        return 0.0
    return round(sum(errors) / len(errors), 2)


def write_markdown(rows: list[dict[str, str]], backtest_rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    completed = [row for row in rows if row.get("status") == "DONE"]
    lines = [
        "# Russell, Kansas Hourly Weather Log",
        "",
        "Hourly beginner forecast for next-hour weather values.",
        "",
        "Model inputs: previous 24-hour values, recent movement, hour of day, day of week, humidity, wind, cloud cover, pressure, and precipitation probability.",
        "",
        "## Live MAE",
        "",
    ]
    for target, unit in TARGETS.items():
        lines.append(f"- {target}: {mean_absolute_error(completed, target)} {unit} across {len(completed)} checked predictions")
    lines.extend(["", "## Backtest MAE", ""])
    for target, unit in TARGETS.items():
        lines.append(f"- {target}: {mean_absolute_error(backtest_rows, target)} {unit} across {len(backtest_rows)} hourly predictions")
    lines.extend([
        "",
        "## Latest live rows",
        "",
        "| Run time | Target hour | Pred temp °F | Actual temp °F | Temp error °F | Pred humidity % | Pred wind mph | Pred cloud % | Pred pressure hPa | Pred precip % | Status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for row in list(reversed(rows[-72:])):
        lines.append(
            f"| {row['run_time']} | {row['target_time']} | {row['predicted_temperature_f']} | "
            f"{row['actual_temperature_f'] or 'waiting'} | {row['absolute_error_temperature_f'] or 'waiting'} | "
            f"{row['predicted_humidity_pct']} | {row['predicted_wind_speed_mph']} | {row['predicted_cloud_cover_pct']} | "
            f"{row['predicted_pressure_hpa']} | {row['predicted_precip_probability_pct']} | {row['status']} |"
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
        f"Russell next-hour weather prediction for {latest['target_time']}: "
        f"temp={latest['predicted_temperature_f']} °F, humidity={latest['predicted_humidity_pct']}%, "
        f"wind={latest['predicted_wind_speed_mph']} mph, cloud={latest['predicted_cloud_cover_pct']}%, "
        f"pressure={latest['predicted_pressure_hpa']} hPa, precip={latest['predicted_precip_probability_pct']}%"
    )
    print(f"Backtest temperature MAE since {month_start}: {mean_absolute_error(backtest_rows, 'temperature_f')} °F")


if __name__ == "__main__":
    main()
