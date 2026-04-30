# Smart Room Digital Twin — Python/Streamlit

A fully functional Digital Twin dashboard that simulates, monitors,
and visualises a room's environment in real time.

---

## Project Structure

```
digital_twin_room/
│
├── app.py                  ← Main Streamlit dashboard (run this)
├── requirements.txt        ← Python dependencies
├── README.md               ← This file
│
├── data/
│   ├── simulate.py         ← Data generation (sine-wave model)
│   └── room_data.csv       ← Auto-generated on first run
│
└── utils/
    └── helpers.py          ← Thresholds, alerts, device logic, prediction
```

---

## Step-by-Step Setup

### Step 1 — Install Python
Make sure Python 3.10 or above is installed.
Check by running:
```
python --version
```
Download from https://www.python.org if needed.

---

### Step 2 — Create a virtual environment (recommended)
```bash
# Create the environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

---

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

This installs:
- streamlit   → dashboard framework
- pandas      → data handling
- plotly      → interactive charts
- numpy       → math support

---

### Step 4 — (Optional) Pre-generate the dataset
```bash
python data/simulate.py
```
This creates `data/room_data.csv` with 3 days × 1440 minutes = 4320 rows.
The app also generates this automatically on first launch.

---

### Step 5 — Run the app
```bash
streamlit run app.py
```
Your browser will open at http://localhost:8501

---

## Dashboard Modes

| Mode | Description |
|---|---|
| Live simulation | Generates one reading per second, updates charts live |
| Historical replay | Replays the 3-day CSV at adjustable speed |
| Static snapshot | Full dataset charts, statistics, download button |

---

## Parameters Tracked

| Parameter | Normal | Warning | Critical |
|---|---|---|---|
| Temperature | < 30 °C | 30–40 °C | > 40 °C |
| Humidity | < 60 % | 60–75 % | > 75 % |
| CO₂ | < 800 ppm | 800–1200 ppm | > 1200 ppm |
| Light | < 500 lux | 500–800 lux | > 800 lux |

---

## Features

- Live updating sensor readings with delta indicators
- Auto-device control (AC, Fan, Humidifier, Dehumidifier trigger automatically)
- Manual device overrides via sidebar toggles
- Colour-coded alerts (Normal / Warning / Critical)
- Line charts with warning/critical threshold lines
- 5-step linear trend prediction shown as dotted line
- Historical replay with progress bar and donut chart
- Full 3-day dataset view with scatter plots
- CSV download button
- Adjustable thresholds via sidebar sliders

---

## How the Simulation Works

Temperature follows a sine-wave day/night cycle:
```
temp = 24 + 10 × sin(2π × (hour − 6) / 24) + noise
```
- Peak (~34 °C) around 12:00–15:00
- Trough (~14 °C) around 04:00–06:00
- Noise: ±0.8 °C random variation

Humidity follows an offset cycle:
```
hum = 50 + 16 × sin(2π × (hour + 4) / 24) + noise
```

CO₂ rises during occupied hours (08:00–22:00).
Light follows a half-sine sunrise/sunset curve.

---

## Report Outline (for submission)

1. **Problem Statement** — Why monitor a room? What is a Digital Twin?
2. **System Design** — Parameters, thresholds, architecture diagram
3. **Data Simulation** — Sine-wave model, noise, CSV generation
4. **Dashboard** — Streamlit, Plotly, three modes
5. **Intelligence** — Threshold alerts, auto device control, trend prediction
6. **Screenshots** — Normal state, Warning state, Critical state, Replay mode
7. **Conclusion** — Findings, limitations, possible extensions

---

## Possible Extensions

- Connect a real DHT11/DHT22 sensor via serial port
- Push data to MQTT broker (IoT)
- Add machine learning anomaly detection (scikit-learn IsolationForest)
- Export PDF report from dashboard
- Add floor-plan 2D visualisation with Plotly shapes
