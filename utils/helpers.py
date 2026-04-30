"""
utils/helpers.py
Threshold definitions, alert logic, and colour helpers used across the app.
"""

# ── Thresholds ────────────────────────────────────────────────────────────────

THRESHOLDS = {
    "temperature_c": {"warning": 30, "critical": 40, "unit": "°C", "label": "Temperature"},
    "humidity_pct":  {"warning": 60, "critical": 75, "unit": "%",  "label": "Humidity"},
    "co2_ppm":       {"warning": 800,"critical": 1200,"unit": "ppm","label": "CO₂"},
    "light_lux":     {"warning": 500,"critical": 800, "unit": "lux","label": "Light"},
}

STATUS_COLORS = {
    "Normal":   "#1D9E75",   # teal-green
    "Warning":  "#EF9F27",   # amber
    "Critical": "#E24B4A",   # red
}

STATUS_BG = {
    "Normal":   "#EAF3DE",
    "Warning":  "#FAEEDA",
    "Critical": "#FCEBEB",
}

METRIC_ICONS = {
    "temperature_c": "🌡️",
    "humidity_pct":  "💧",
    "co2_ppm":       "🌿",
    "light_lux":     "☀️",
}


# ── Classification ────────────────────────────────────────────────────────────

def classify(value: float, key: str) -> str:
    t = THRESHOLDS[key]
    if value >= t["critical"]:
        return "Critical"
    if value >= t["warning"]:
        return "Warning"
    return "Normal"


def overall_status(row: dict) -> str:
    statuses = [classify(row[k], k) for k in THRESHOLDS]
    if "Critical" in statuses:
        return "Critical"
    if "Warning" in statuses:
        return "Warning"
    return "Normal"


# ── Alert generation ──────────────────────────────────────────────────────────

def build_alerts(row: dict) -> list[dict]:
    alerts = []
    messages = {
        "temperature_c": {
            "Warning":  "Temperature elevated ({val}°C). Consider switching on AC.",
            "Critical": "Temperature critical ({val}°C)! Immediate cooling required.",
        },
        "humidity_pct": {
            "Warning":  "Humidity elevated ({val}%). Ventilate the room.",
            "Critical": "Humidity critical ({val}%)! Risk of mould — dehumidify now.",
        },
        "co2_ppm": {
            "Warning":  "CO₂ rising ({val} ppm). Open a window.",
            "Critical": "CO₂ critical ({val} ppm)! Poor air quality — ventilate immediately.",
        },
        "light_lux": {
            "Warning":  "Light levels high ({val} lux). Blinds recommended.",
            "Critical": "Extreme light ({val} lux). Direct sunlight exposure.",
        },
    }
    for key, msgs in messages.items():
        status = classify(row[key], key)
        if status in msgs:
            alerts.append({
                "status": status,
                "message": msgs[status].format(val=row[key]),
                "param": THRESHOLDS[key]["label"],
            })
    return alerts


# ── Device auto-logic ─────────────────────────────────────────────────────────

def auto_devices(temp: float, hum: float) -> dict:
    """Simple rule-based device control."""
    return {
        "AC":         temp >= 32,
        "Fan":        28 <= temp < 32,
        "Humidifier": hum < 35,
        "Dehumidifier": hum >= 65,
        "Alarm":      temp >= 40 or hum >= 75,
    }


# ── Prediction ────────────────────────────────────────────────────────────────

def predict_next(series: list[float], steps: int = 5) -> list[float]:
    """Naive linear trend extrapolation over the last 10 readings."""
    if len(series) < 2:
        return [series[-1]] * steps
    recent = series[-10:]
    n = len(recent)
    avg_delta = (recent[-1] - recent[0]) / max(n - 1, 1)
    return [round(recent[-1] + avg_delta * (i + 1), 1) for i in range(steps)]
