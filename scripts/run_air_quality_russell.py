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
PLACE = "Russell, Kansas"
AQ_FIELDS = ["pm10", "pm2_5", "carbon_monoxide", "nitrogen_dioxide", "ozone"]
TARGETS = {
    "pm10": "ug_m3",
    "pm2_5": "ug_m3",
    "carbon_monoxide": "ug_m3",
    "nitrogen_dioxide": "ug_m3",
    "ozone": "ug_m3",
}


def fetch_air_quality(latitude: float = RUSSELL_LAT, longitude: float = RUSSELL_LON) -> list[dict[str, object]]:
    params = urllib.parse.urlencode(
        {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": ",".join(AQ_FIELDS),
            "timezone": "UTC",
            "past_days": 7,
            "forecast_days": 2,
        }
    )
    req = urllib.request.Request(
        f"https://air-quality-api.open-meteo.com/v1/air-quality?{params}",
        headers={"User-Agent": "timeseries-practice"},
    )
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
        }
        for field in AQ_FIELDS:
            values = hourly.get(field, [None] * len(times))
            row[field] = None if values[i] is None else round(float(values[i]), 2)
        if row["pm2_5"] is not None:
            rows.append(row)
    return rows


def predict_value(history: list[dict[str, object]], target: str, lookback: int = 3) -> float:
    clean = [row for row in history if row.get(target) is not None]
    if len(clean) < lookback + 1:
        raise ValueError(f"not enough rows for {target}")
    values = [float(row[target]) for row in clean]
    changes = [values[i] - values[i - 1] for i in range(1, len(values))]
    momentum_prediction = values[-1] + sum(changes[-lookback:]) / lookback
    if len(clean) >= 24:
        prediction = 0.55 * float(clean[-24][target]) + 0.45 * momentum_prediction
    else:
        prediction = momentum_prediction
    return round(max(0.0, prediction), 2)


def predict_all(history: list[dict[str, object]], lookback: int) -> dict[str, float]:
    return {target: predict_value(history, target, lookback) for target in TARGETS}


def fieldnames() -> list[str]:
    cols = ["run_time", "place", "from_time", "target_time", "hour_utc", "day_of_week", "status"]
    for target in TARGETS:
        cols += [f"predicted_{target}", f"actual_{target}", f"absolute_error_{target}"]
    return cols


def load_log(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_log(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames())
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
            pred = float(row[f"predicted_{target}"])
            row[f"actual_{target}"] = str(round(float(actual), 2))
            row[f"absolute_error_{target}"] = str(round(abs(float(actual) - pred), 2))
        row["status"] = "DONE"


def append_next_prediction(rows: list[dict[str, str]], aq_rows: list[dict[str, object]], lookback: int) -> None:
    now = datetime.now(timezone.utc)
    past_or_now = [row for row in aq_rows if datetime.fromisoformat(str(row["time"])) <= now]
    if len(past_or_now) < lookback + 1:
        past_or_now = aq_rows[: lookback + 1]
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lookback", type=int, default=3)
    parser.add_argument("--csv", default="reports/air_quality_russell.csv")
    args = parser.parse_args()

    aq_rows = fetch_air_quality()
    log_rows = load_log(Path(args.csv))
    update_pending(log_rows, aq_rows)
    append_next_prediction(log_rows, aq_rows, args.lookback)
    save_log(Path(args.csv), log_rows)
    latest = log_rows[-1]
    print(
        f"Russell AQ next-hour prediction for {latest['target_time']}: "
        f"pm2_5={latest['predicted_pm2_5']}, pm10={latest['predicted_pm10']}, "
        f"ozone={latest['predicted_ozone']}, no2={latest['predicted_nitrogen_dioxide']}"
    )


if __name__ == "__main__":
    main()
