"""
app.py  —  Smart Room Digital Twin
Run with:  streamlit run app.py
"""

import time
import os
import sys
import math
import random


import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# ── path fix so utils/ is importable ─────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from utils.helpers import (
    THRESHOLDS, STATUS_COLORS, STATUS_BG, METRIC_ICONS,
    classify, overall_status, build_alerts, auto_devices, predict_next,
)
from data.simulate import generate_data, save_csv

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Smart Room — Digital Twin",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Metric card */
[data-testid="metric-container"] {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 12px;
    padding: 16px !important;
}
/* Status badge */
.status-badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 100px;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.03em;
}
/* Alert box */
.alert-box {
    padding: 12px 16px;
    border-radius: 10px;
    margin-bottom: 8px;
    font-size: 14px;
    border-left: 4px solid;
}
.alert-Critical { background:#FCEBEB; border-color:#E24B4A; color:#501313; }
.alert-Warning  { background:#FAEEDA; border-color:#EF9F27; color:#412402; }
.alert-Normal   { background:#EAF3DE; border-color:#1D9E75; color:#173404; }
/* Section headers */
.section-header {
    font-size: 13px;
    font-weight: 600;
    color: #6c757d;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin: 20px 0 10px;
    border-bottom: 1px solid #dee2e6;
    padding-bottom: 6px;
}
/* Device pill */
.device-pill {
    display: inline-block;
    padding: 5px 14px;
    border-radius: 100px;
    font-size: 13px;
    font-weight: 500;
    margin: 3px 4px;
}
.device-on  { background:#EAF3DE; color:#0F6E56; border:1px solid #9FE1CB; }
.device-off { background:#f1f3f5; color:#868e96; border:1px solid #dee2e6; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ══════════════════════════════════════════════════════════════════════════════

CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "room_data.csv")

@st.cache_data(show_spinner="Generating simulation data…")
def load_data() -> pd.DataFrame:
    if not os.path.exists(CSV_PATH):
        records = generate_data(days=3)
        save_csv(records, CSV_PATH)
    df = pd.read_csv(CSV_PATH, parse_dates=["datetime"])
    return df


df_full = load_data()


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — CONTROLS
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2038/2038854.png", width=60)
    st.title("Digital Twin")
    st.caption("Smart Room Monitor — v1.0")
    st.divider()

    st.markdown("### ⚙️ Simulation Controls")

    mode = st.radio(
        "Dashboard mode",
        ["Live simulation", "Historical replay", "Static snapshot"],
        index=0,
    )

    if mode == "Historical replay":
        day_select = st.selectbox("Select day", options=[1, 2, 3], index=0)
        df_day = df_full[df_full["day"] == day_select].reset_index(drop=True)
        replay_speed = st.slider("Replay speed (rows/sec)", 1, 30, 5)

    st.divider()
    st.markdown("### 🎛️ Manual Overrides")
    manual_ac  = st.toggle("Force AC ON",  value=False)
    manual_fan = st.toggle("Force Fan ON", value=False)
    manual_hum = st.toggle("Force Humidifier ON", value=False)

    st.divider()
    st.markdown("### 🔔 Alert Thresholds")
    temp_warn = st.slider("Temp warning (°C)",  20, 45, 30)
    temp_crit = st.slider("Temp critical (°C)", 25, 55, 40)
    hum_warn  = st.slider("Humidity warning (%)", 30, 80, 60)
    hum_crit  = st.slider("Humidity critical (%)", 40, 95, 75)

    # Update thresholds dynamically
    THRESHOLDS["temperature_c"]["warning"]  = temp_warn
    THRESHOLDS["temperature_c"]["critical"] = temp_crit
    THRESHOLDS["humidity_pct"]["warning"]   = hum_warn
    THRESHOLDS["humidity_pct"]["critical"]  = hum_crit

    st.divider()
    if st.button("🔄 Regenerate dataset"):
        os.remove(CSV_PATH) if os.path.exists(CSV_PATH) else None
        st.cache_data.clear()
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# HELPER — draw a single plotly line chart
# ══════════════════════════════════════════════════════════════════════════════

def line_chart(df_slice: pd.DataFrame, col: str, warn: float, crit: float,
               color: str = "#378ADD", title: str = "") -> go.Figure:
    meta = THRESHOLDS[col]
    fig = go.Figure()

    # Main line
    fig.add_trace(go.Scatter(
        x=df_slice["datetime"], y=df_slice[col],
        mode="lines", line=dict(color=color, width=2),
        name=meta["label"], hovertemplate=f"%{{y}} {meta['unit']}<extra></extra>",
    ))

    # Prediction (last 5 points extrapolated)
    preds = predict_next(df_slice[col].tolist(), steps=6)
    last_dt = df_slice["datetime"].iloc[-1]
    pred_times = pd.date_range(last_dt, periods=7, freq="min")[1:]
    fig.add_trace(go.Scatter(
        x=pred_times, y=preds,
        mode="lines", line=dict(color=color, width=1.5, dash="dot"),
        name="Predicted", hovertemplate=f"%{{y}} {meta['unit']}<extra>predicted</extra>",
    ))

    # Threshold lines
    x_range = [df_slice["datetime"].iloc[0], pred_times[-1]]
    fig.add_shape(type="line", x0=x_range[0], x1=x_range[1],
                  y0=warn, y1=warn, line=dict(color="#EF9F27", width=1.2, dash="dash"))
    fig.add_shape(type="line", x0=x_range[0], x1=x_range[1],
                  y0=crit, y1=crit, line=dict(color="#E24B4A", width=1.2, dash="dash"))

    fig.add_annotation(x=x_range[1], y=warn, text="⚠ Warn", showarrow=False,
                       font=dict(size=10, color="#EF9F27"), xanchor="right")
    fig.add_annotation(x=x_range[1], y=crit, text="🔴 Critical", showarrow=False,
                       font=dict(size=10, color="#E24B4A"), xanchor="right")

    fig.update_layout(
        title=dict(text=title, font=dict(size=13)),
        margin=dict(l=10, r=10, t=30, b=10),
        height=220,
        xaxis=dict(showgrid=False, title=None),
        yaxis=dict(gridcolor="#f0f0f0", title=meta["unit"]),
        legend=dict(orientation="h", y=-0.2),
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="x unified",
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# LIVE SIMULATION MODE
# ══════════════════════════════════════════════════════════════════════════════

def live_simulation():
    st.markdown("## 🏠 Smart Room — Digital Twin Dashboard")
    st.caption("Live simulation — data updates every second")

    # session state for history
    if "history" not in st.session_state:
        st.session_state.history = []
    if "tick" not in st.session_state:
        st.session_state.tick = 0

    tick = st.session_state.tick
    hist = st.session_state.history

    # Generate one reading
    minute = tick % 1440
    temp = round(24 + 10 * math.sin(2 * math.pi * (minute / 60 - 6) / 24)
                 + random.uniform(-0.8, 0.8)
                 - (4.0 if manual_ac else 0) - (1.5 if manual_fan else 0), 1)
    hum  = round(min(max(50 + 16 * math.sin(2 * math.pi * (minute / 60 + 4) / 24)
                 + random.uniform(-2, 2) + (8 if manual_hum else 0), 20), 95), 1)
    co2  = int(700 + 300 * math.sin(math.pi * max(0, (minute / 60 - 8)) / 14)
               + random.randint(-20, 20)) if 8 <= minute / 60 <= 22 else random.randint(400, 460)
    lux  = max(0, int(600 * math.sin(math.pi * (minute / 60 - 6) / 12)
               + random.randint(-30, 30))) if 6 <= minute / 60 <= 18 else random.randint(0, 10)

    row = {
        "datetime": pd.Timestamp.now(),
        "temperature_c": temp, "humidity_pct": hum,
        "co2_ppm": co2, "light_lux": lux,
    }
    hist.append(row)
    if len(hist) > 120:
        hist.pop(0)

    df_live = pd.DataFrame(hist)
    devices = auto_devices(temp, hum)
    if manual_ac:  devices["AC"] = True
    if manual_fan: devices["Fan"] = True
    if manual_hum: devices["Humidifier"] = True
    alerts = build_alerts(row)
    status = overall_status(row)

    # ── Top status bar ──────────────────────────────────────────────────────
    col_s1, col_s2, col_s3 = st.columns([2, 1, 1])
    with col_s1:
        color = STATUS_COLORS[status]
        bg    = STATUS_BG[status]
        st.markdown(
            f'<div style="background:{bg};border-left:4px solid {color};'
            f'padding:10px 16px;border-radius:8px;font-weight:600;color:{color};">'
            f'System Status: {status}</div>', unsafe_allow_html=True)
    with col_s2:
        st.metric("Simulated Hour", f"{int(minute/60):02d}:{minute%60:02d}")
    with col_s3:
        st.metric("Day", f"Day {tick // 1440 + 1}")

    st.markdown('<div class="section-header">Live Readings</div>', unsafe_allow_html=True)

    # ── Metric cards ────────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    prev = hist[-2] if len(hist) >= 2 else row

    for col_obj, key, label, icon in [
        (m1, "temperature_c", "Temperature", "🌡️"),
        (m2, "humidity_pct",  "Humidity",    "💧"),
        (m3, "co2_ppm",       "CO₂",         "🌿"),
        (m4, "light_lux",     "Light",       "☀️"),
    ]:
        val  = row[key]
        prev_val = prev[key]
        meta = THRESHOLDS[key]
        s    = classify(val, key)
        with col_obj:
            st.metric(
                label=f"{icon} {label}",
                value=f"{val} {meta['unit']}",
                delta=f"{round(val - prev_val, 1)} {meta['unit']}",
            )
            st.markdown(
                f'<span class="status-badge" style="background:{STATUS_BG[s]};'
                f'color:{STATUS_COLORS[s]};">{s}</span>',
                unsafe_allow_html=True,
            )

    # ── Devices ─────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Device Status (Auto-Control)</div>',
                unsafe_allow_html=True)
    dev_html = ""
    for name, on in devices.items():
        cls = "device-on" if on else "device-off"
        icon = "✅" if on else "⭕"
        dev_html += f'<span class="device-pill {cls}">{icon} {name}</span>'
    st.markdown(dev_html, unsafe_allow_html=True)

    # ── Alerts ──────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Alerts</div>', unsafe_allow_html=True)
    if not alerts:
        st.markdown('<div class="alert-box alert-Normal">✅ All parameters within normal range.</div>',
                    unsafe_allow_html=True)
    for a in alerts:
        st.markdown(
            f'<div class="alert-box alert-{a["status"]}"><b>{a["param"]}:</b> {a["message"]}</div>',
            unsafe_allow_html=True)

    # ── Charts ──────────────────────────────────────────────────────────────
    if len(df_live) >= 3:
        st.markdown('<div class="section-header">Sensor Trends (live, last 120 readings)</div>',
                    unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(
                line_chart(df_live, "temperature_c", temp_warn, temp_crit,
                           "#D85A30", "🌡️ Temperature over time"),
                use_container_width=True, key="live_temp")
        with c2:
            st.plotly_chart(
                line_chart(df_live, "humidity_pct", hum_warn, hum_crit,
                           "#378ADD", "💧 Humidity over time"),
                use_container_width=True, key="live_hum")

        c3, c4 = st.columns(2)
        with c3:
            st.plotly_chart(
                line_chart(df_live, "co2_ppm", 800, 1200,
                           "#1D9E75", "🌿 CO₂ over time"),
                use_container_width=True, key="live_co2")
        with c4:
            st.plotly_chart(
                line_chart(df_live, "light_lux", 500, 800,
                           "#EF9F27", "☀️ Light level over time"),
                use_container_width=True, key="live_lux")

    st.session_state.tick += 1
    time.sleep(1)
    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# HISTORICAL REPLAY MODE
# ══════════════════════════════════════════════════════════════════════════════

def historical_replay():
    st.markdown("## 📅 Historical Replay")

    if "replay_idx" not in st.session_state:
        st.session_state.replay_idx = 0

    idx = min(st.session_state.replay_idx, len(df_day) - 1)
    df_slice = df_day.iloc[: idx + 1]
    row = df_day.iloc[idx].to_dict()
    status = row["status"]

    # Progress bar
    st.progress((idx + 1) / len(df_day), text=f"Time: {row['datetime']}  ({idx+1}/{len(df_day)} mins)")

    # Metrics
    m1, m2, m3, m4 = st.columns(4)
    for col_obj, key, icon in [
        (m1, "temperature_c", "🌡️"),
        (m2, "humidity_pct",  "💧"),
        (m3, "co2_ppm",       "🌿"),
        (m4, "light_lux",     "☀️"),
    ]:
        meta = THRESHOLDS[key]
        s = classify(row[key], key)
        with col_obj:
            st.metric(f"{icon} {meta['label']}", f"{row[key]} {meta['unit']}")
            st.markdown(
                f'<span class="status-badge" style="background:{STATUS_BG[s]};color:{STATUS_COLORS[s]};">{s}</span>',
                unsafe_allow_html=True)

    # Charts
    if len(df_slice) >= 2:
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(
                line_chart(df_slice, "temperature_c", temp_warn, temp_crit,
                           "#D85A30", "Temperature"),
                use_container_width=True, key="rep_temp")
        with c2:
            st.plotly_chart(
                line_chart(df_slice, "humidity_pct", hum_warn, hum_crit,
                           "#378ADD", "Humidity"),
                use_container_width=True, key="rep_hum")

    # Status distribution donut
    if len(df_slice) > 10:
        counts = df_slice["status"].value_counts().reset_index()
        counts.columns = ["status", "count"]
        fig = px.pie(counts, names="status", values="count", hole=0.55,
                     color="status",
                     color_discrete_map=STATUS_COLORS,
                     title="Status distribution so far")
        fig.update_layout(height=280, margin=dict(t=40, b=10))
        st.plotly_chart(fig, use_container_width=True, key="rep_donut")

    # Advance replay
    if st.session_state.replay_idx < len(df_day) - 1:
        time.sleep(1.0 / replay_speed)
        st.session_state.replay_idx += 1
        st.rerun()
    else:
        st.success("Replay complete for this day.")
        if st.button("Replay again"):
            st.session_state.replay_idx = 0
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STATIC SNAPSHOT MODE
# ══════════════════════════════════════════════════════════════════════════════

def static_snapshot():
    st.markdown("## 📊 Full Dataset Analysis")

    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Temperature", "Humidity", "Raw Data"])

    with tab1:
        st.markdown("### 3-Day Summary Statistics")
        stats = df_full[["temperature_c", "humidity_pct", "co2_ppm", "light_lux"]].describe().T
        stats.index = ["Temperature (°C)", "Humidity (%)", "CO₂ (ppm)", "Light (lux)"]
        st.dataframe(stats.round(2), use_container_width=True)

        st.markdown("### Status Distribution (all 3 days)")
        counts = df_full["status"].value_counts().reset_index()
        counts.columns = ["Status", "Minutes"]
        fig_bar = px.bar(counts, x="Status", y="Minutes",
                         color="Status", color_discrete_map=STATUS_COLORS,
                         text="Minutes")
        fig_bar.update_layout(height=300, plot_bgcolor="white",
                              paper_bgcolor="white", showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        fig_temp = px.line(df_full, x="datetime", y="temperature_c",
                           color="day", title="Temperature — 3-day view",
                           labels={"temperature_c": "°C", "datetime": "Time"})
        fig_temp.add_hline(y=temp_warn, line_dash="dash", line_color="#EF9F27",
                           annotation_text="Warning")
        fig_temp.add_hline(y=temp_crit, line_dash="dash", line_color="#E24B4A",
                           annotation_text="Critical")
        fig_temp.update_layout(height=380, plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig_temp, use_container_width=True)

    with tab3:
        fig_hum = px.line(df_full, x="datetime", y="humidity_pct",
                          color="day", title="Humidity — 3-day view",
                          labels={"humidity_pct": "%", "datetime": "Time"})
        fig_hum.add_hline(y=hum_warn, line_dash="dash", line_color="#EF9F27",
                          annotation_text="Warning")
        fig_hum.add_hline(y=hum_crit, line_dash="dash", line_color="#E24B4A",
                          annotation_text="Critical")
        fig_hum.update_layout(height=380, plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig_hum, use_container_width=True)

        # Scatter: temp vs humidity
        fig_scatter = px.scatter(df_full, x="temperature_c", y="humidity_pct",
                                 color="status", color_discrete_map=STATUS_COLORS,
                                 opacity=0.4, title="Temperature vs Humidity (coloured by status)")
        fig_scatter.update_layout(height=340, plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig_scatter, use_container_width=True)

    with tab4:
        st.dataframe(df_full, use_container_width=True, height=400)
        csv_bytes = df_full.to_csv(index=False).encode()
        st.download_button("⬇️ Download CSV", csv_bytes,
                           "room_data.csv", "text/csv")


# ══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════════════════════

if mode == "Live simulation":
    live_simulation()
elif mode == "Historical replay":
    historical_replay()
else:
    static_snapshot()
