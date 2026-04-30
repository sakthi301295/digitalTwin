"""
simulate.py
Generates a 24-hour simulated room dataset and saves it to room_data.csv
Run once before launching the dashboard, or call generate_data() from app.py
"""

import math
import random
import csv
import os
from datetime import datetime, timedelta


def get_temperature(minute: int, ac_on: bool = False, fan_on: bool = False) -> float:
    """Sine-wave day/night cycle with random noise."""
    hour = minute / 60
    base = 24 + 10 * math.sin(2 * math.pi * (hour - 6) / 24)
    noise = random.uniform(-0.8, 0.8)
    val = base + noise
    if ac_on:
        val -= 4.0
    if fan_on:
        val -= 1.5
    return round(val, 1)


def get_humidity(minute: int, humidifier_on: bool = False) -> float:
    """Humidity peaks in early morning and mid-afternoon."""
    hour = minute / 60
    base = 50 + 16 * math.sin(2 * math.pi * (hour + 4) / 24)
    noise = random.uniform(-2.0, 2.0)
    val = base + noise
    if humidifier_on:
        val += 8
    return round(min(max(val, 20), 95), 1)


def get_co2(minute: int) -> int:
    """CO2 ppm — rises during occupied hours (8am–10pm)."""
    hour = minute / 60
    if 8 <= hour <= 22:
        base = 700 + 300 * math.sin(math.pi * (hour - 8) / 14)
    else:
        base = 420 + 50 * random.random()
    return int(base + random.randint(-20, 20))


def get_light_lux(minute: int) -> int:
    """Daylight lux with sunrise/sunset curve."""
    hour = minute / 60
    if 6 <= hour <= 18:
        lux = 600 * math.sin(math.pi * (hour - 6) / 12)
        return max(0, int(lux + random.randint(-30, 30)))
    return random.randint(0, 10)


def classify_status(temp: float, hum: float) -> str:
    if temp >= 40 or hum >= 75:
        return "Critical"
    if temp >= 30 or hum >= 60:
        return "Warning"
    return "Normal"


def generate_data(days: int = 1, seed: int = 42) -> list[dict]:
    random.seed(seed)
    records = []
    base_dt = datetime(2024, 1, 1, 0, 0)

    for day in range(days):
        for minute in range(1440):
            total_min = day * 1440 + minute
            dt = base_dt + timedelta(minutes=total_min)
            temp = get_temperature(minute)
            hum = get_humidity(minute)
            co2 = get_co2(minute)
            lux = get_light_lux(minute)
            status = classify_status(temp, hum)

            records.append({
                "datetime": dt.strftime("%Y-%m-%d %H:%M"),
                "day": day + 1,
                "minute": minute,
                "hour": round(minute / 60, 2),
                "temperature_c": temp,
                "humidity_pct": hum,
                "co2_ppm": co2,
                "light_lux": lux,
                "status": status,
            })

    return records


def save_csv(records: list[dict], path: str = "data/room_data.csv") -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    return path


if __name__ == "__main__":
    print("Generating 3-day simulation dataset...")
    data = generate_data(days=3)
    path = save_csv(data, "data/room_data.csv")
    print(f"Saved {len(data)} records to {path}")
    normals  = sum(1 for r in data if r["status"] == "Normal")
    warnings = sum(1 for r in data if r["status"] == "Warning")
    crits    = sum(1 for r in data if r["status"] == "Critical")
    print(f"  Normal: {normals} | Warning: {warnings} | Critical: {crits}")
