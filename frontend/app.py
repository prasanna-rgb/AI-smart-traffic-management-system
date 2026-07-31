"""
Streamlit Frontend Web Dashboard - Professional White Light Edition.
Enterprise AI Smart Traffic Management System UI with real-time telemetry, Google Maps, PyDeck GIS, PDF exporter, and voice alerts.
"""
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
from datetime import datetime
import pydeck as pdk

try:
    import folium
    from streamlit_folium import st_folium
    FOLIUM_AVAILABLE = True
except Exception:
    FOLIUM_AVAILABLE = False

from config.settings import APP_NAME, VERSION, API_HOST, API_PORT
from database.db import (
    init_db,
    get_latest_reports,
    get_latest_traffic_data,
    get_active_alerts,
    get_analytics_summary
)
from tools.simulation_tools import TrafficSimulator, ROADS
from tools.pdf_generator import generate_traffic_pdf_report
from tools.audio_announcer import generate_voice_announcement_html
from tools.whatsapp_bot import send_whatsapp_ai_bot_message
from tools.traffic_data_fetcher import TrafficDataFetcher, get_data_lineage

from tools.sms_bot import send_cellular_sms
from crew import run_traffic_crew

# Ensure DB initialized
init_db()

# Page Setup
st.set_page_config(
    page_title="Smart City Traffic Control Hub | Technical Dark",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# GPS Coordinates dictionary for city junctions
ROAD_COORDINATES = {
    "Main Road": {"lat": 12.9716, "lon": 77.5946},
    "Broadway Ave": {"lat": 12.9800, "lon": 77.6000},
    "Express Highway": {"lat": 12.9600, "lon": 77.6100},
    "Downtown Ring": {"lat": 12.9650, "lon": 77.5850},
    "Harbor View Park": {"lat": 12.9850, "lon": 77.5750}
}

# Inject High-Tech Cyber Dark CSS Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: #0B0F19 !important;
        color: #F8FAFC !important;
    }

    /* Technical Dark Base Container */
    .stApp, [data-testid="stAppViewContainer"] {
        background-color: #0B0F19 !important;
        color: #F8FAFC !important;
    }

    /* Streamlit Top Navbar Header Dark Mode Fix */
    header[data-testid="stHeader"], [data-testid="stHeader"], .stHeader, [data-testid="stToolbar"], [data-testid="stDecoration"], nav, header {
        background-color: #0B0F19 !important;
        background: #0B0F19 !important;
        color: #F8FAFC !important;
    }
    header[data-testid="stHeader"] *, [data-testid="stHeader"] * {
        color: #F8FAFC !important;
    }

    /* Top Navigation & Headings */
    h1, h2, h3, h4, h5, h6, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }


    p, span, label, legend, [data-testid="stWidgetLabel"] {
        color: #E2E8F0 !important;
    }

    /* Subheaders & Captions */
    .stCaption, small, [data-testid="stCaptionContainer"] * {
        color: #9CA3AF !important;
        font-weight: 500 !important;
    }

    /* BaseWeb Dropdown Popover Menus & Selectboxes (Fixes White Screen & Invisible Options) */
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"], li[role="option"], [data-baseweb="popover"] *, [data-baseweb="menu"] * {
        background-color: #1E293B !important;
        color: #F8FAFC !important;
        border-color: #334155 !important;
    }
    li[role="option"]:hover, div[role="option"]:hover, [data-baseweb="menu"] li:hover {
        background-color: #0284C7 !important;
        color: #FFFFFF !important;
    }
    div[data-baseweb="select"] > div, div[data-baseweb="select"] input {
        background-color: #1E293B !important;
        color: #F8FAFC !important;
        border-color: #334155 !important;
    }
    div[data-baseweb="select"] svg {
        fill: #F8FAFC !important;
    }
    div[data-baseweb="select"] p, div[data-baseweb="select"] span {
        color: #F8FAFC !important;
    }

    /* Streamlit Alert Callouts (info, success, warning, error) */
    div[data-testid="stAlert"] {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }
    div[data-testid="stAlert"] p, div[data-testid="stAlert"] div, div[data-testid="stAlert"] span {
        color: #F8FAFC !important;
    }

    /* Top Cyber Navigation Bar Header */
    .top-nav {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #111827 !important;
        border: 1px solid #1F2937;
        border-left: 4px solid #00F2FE;
        padding: 0.9rem 1.4rem;
        border-radius: 10px;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 20px rgba(0, 242, 254, 0.05);
    }

    .brand-title {
        font-size: 1.35rem;
        font-weight: 800;
        color: #F3F4F6 !important;
        letter-spacing: -0.01em;
    }

    .brand-sub {
        font-size: 0.8rem;
        color: #9CA3AF !important;
        font-family: 'JetBrains Mono', monospace;
    }

    .badge-online {
        background-color: rgba(16, 185, 129, 0.15) !important;
        color: #10B981 !important;
        border: 1px solid #059669;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
    }

    /* High-Tech Dark Metric Boxes */
    .metric-box {
        background: #111827 !important;
        border: 1px solid #1F2937;
        border-radius: 10px;
        padding: 1.1rem 1.3rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }

    .metric-box:hover {
        transform: translateY(-2px);
        border-color: #00F2FE;
    }

    .metric-head {
        color: #9CA3AF !important;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-family: 'JetBrains Mono', monospace;
    }

    .metric-body {
        color: #00F2FE !important;
        font-size: 1.9rem;
        font-weight: 800;
        margin-top: 0.2rem;
        font-family: 'JetBrains Mono', monospace;
    }

    .metric-sub {
        font-size: 0.75rem;
        color: #6B7280 !important;
        margin-top: 0.2rem;
    }

    /* Alert Banners (Dark Tech Theme) */
    .banner-critical {
        background-color: #450A0A !important;
        border: 1px solid #EF4444;
        color: #FCA5A5 !important;
        padding: 0.9rem 1.2rem;
        border-radius: 8px;
        font-weight: 600;
        margin-bottom: 1.2rem;
    }

    .banner-critical * {
        color: #FCA5A5 !important;
    }

    .banner-warning {
        background-color: #451A03 !important;
        border: 1px solid #F59E0B;
        color: #FDE68A !important;
        padding: 0.9rem 1.2rem;
        border-radius: 8px;
        font-weight: 600;
        margin-bottom: 1.2rem;
    }

    .banner-warning * {
        color: #FDE68A !important;
    }

    /* Agent Row Cards (Dark Tech Theme) */
    .agent-row-card {
        background: #111827 !important;
        border: 1px solid #1F2937;
        border-left: 3px solid #00F2FE;
        border-radius: 10px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
    }

    .agent-row-card p {
        color: #D1D5DB !important;
    }

    .agent-title-text {
        font-size: 0.95rem;
        font-weight: 700;
        color: #00F2FE !important;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Sidebar Container Styling (Dark High Contrast) */
    [data-testid="stSidebar"], [data-testid="stSidebarNav"], section[data-testid="stSidebar"] {
        background-color: #0D1322 !important;
        border-right: 1px solid #1F2937 !important;
    }

    [data-testid="stSidebar"] *, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label, [data-testid="stSidebar"] li, [data-testid="stSidebar"] strong, [data-testid="stSidebar"] div, [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #F8FAFC !important;
    }

    /* Sidebar Download Buttons & Action Buttons (Fixes White Button & Invisible Text) */
    [data-testid="stSidebar"] button, 
    [data-testid="stSidebar"] a, 
    [data-testid="stSidebar"] [data-testid="stDownloadButton"] a, 
    [data-testid="stSidebar"] [data-testid="stDownloadButton"] button,
    .stDownloadButton button, 
    .stDownloadButton a, 
    button[kind="secondary"], 
    button[kind="primary"], 
    button[data-testid="baseButton-secondary"], 
    button[data-testid="baseButton-primary"],
    a[data-testid="stDownloadButton"] {
        background-color: #1E293B !important;
        background: #1E293B !important;
        color: #38BDF8 !important;
        border: 1px solid #00F2FE !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        text-decoration: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 2px 8px rgba(0, 242, 254, 0.15) !important;
    }

    [data-testid="stSidebar"] button *, 
    [data-testid="stSidebar"] a *, 
    [data-testid="stSidebar"] [data-testid="stDownloadButton"] *, 
    .stDownloadButton *, 
    button[kind="secondary"] *, 
    button[kind="primary"] * {
        color: #38BDF8 !important;
    }

    [data-testid="stSidebar"] button:hover, 
    [data-testid="stSidebar"] a:hover, 
    [data-testid="stSidebar"] [data-testid="stDownloadButton"] a:hover, 
    [data-testid="stSidebar"] [data-testid="stDownloadButton"] button:hover,
    .stDownloadButton button:hover, 
    .stDownloadButton a:hover,
    button[kind="secondary"]:hover, 
    button[kind="primary"]:hover {
        background-color: #00F2FE !important;
        background: #00F2FE !important;
        color: #0B0F19 !important;
        border-color: #00F2FE !important;
        box-shadow: 0 0 15px rgba(0, 242, 254, 0.5) !important;
    }

    [data-testid="stSidebar"] button:hover *, 
    [data-testid="stSidebar"] a:hover *, 
    [data-testid="stSidebar"] [data-testid="stDownloadButton"] a:hover *, 
    .stDownloadButton button:hover * {
        color: #0B0F19 !important;
    }

    /* Form Text Inputs & Text Areas */

    div[data-baseweb="input"] input, textarea, div[data-baseweb="textarea"] textarea {
        background-color: #1E293B !important;
        color: #F8FAFC !important;
        border: 1px solid #334155 !important;
        font-size: 0.95rem !important;
    }

    /* Code Blocks & Pre Blocks */
    div[data-testid="stCodeBlock"], pre, code, .stCodeBlock code {
        background-color: #0F172A !important;
        color: #38BDF8 !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }
    div[data-testid="stCodeBlock"] * {
        color: #38BDF8 !important;
    }

    /* Streamlit DataFrame Tables */
    [data-testid="stDataFrame"], div[data-testid="stTable"], table {
        background-color: #111827 !important;
        color: #F3F4F6 !important;
    }

    [data-testid="stDataFrame"] *, table * {
        color: #F3F4F6 !important;
    }

    /* Tab Custom Styling (Dark Cyber Theme) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: #111827 !important;
        padding: 6px;
        border-radius: 8px;
        border: 1px solid #1F2937;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        color: #9CA3AF !important;
        font-weight: 600;
        font-size: 0.88rem;
        padding: 6px 16px;
    }

    .stTabs [aria-selected="true"] {
        background-color: #00F2FE !important;
        color: #0B0F19 !important;
        font-weight: 800 !important;
        box-shadow: 0 0 10px rgba(0, 242, 254, 0.4);
    }


    .stTabs [aria-selected="true"] * {
        color: #0B0F19 !important;
    }
</style>
""", unsafe_allow_html=True)

# Top Cyber Navbar Header
st.markdown(f"""
<div class='top-nav'>
    <div>
        <div class='brand-title'>🚦 {APP_NAME} <span style='font-size: 0.85rem; color: #00F2FE; font-weight: bold;'>| Technical Dark Edition</span></div>
        <div class='brand-sub'>SYSTEM CONTROL HUD // CrewAI Multi-Agent Traffic Optimization Platform v{VERSION}</div>
    </div>
    <div>
        <span class='badge-online'>● SYSTEM OPERATIONAL</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar Configuration
st.sidebar.markdown("### 🎛️ Control Center")
selected_road = st.sidebar.selectbox("Active Monitoring Junction", ROADS)

# Add explicit manual refresh button
refresh_requested = st.sidebar.button("🔄 Refresh Traffic Data", use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📱 Registered Commuter Phone Number")
reg_phone = st.sidebar.text_input("Mobile Number for AI Auto-Alerts", value="+916383258373", help="When Emergency, Accident, or Congestion >70 trigger automatically, AI dispatches WhatsApp & SMS to this number!")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🌐 Data Source Engine")
sim_mode = st.sidebar.radio("Telemetry Data Source", ["🌐 Live Real-Time API Data Feed (Open-Meteo & Live GPS)", "Manual Scenario Injection"])

# Track state keys
road_telemetry_key = f"cached_telemetry_{selected_road}"
road_report_key = f"cached_report_{selected_road}"
session_key = f"traffic_state_{selected_road}"
road_changed_key = f"active_road_cache"

road_changed = st.session_state.get(road_changed_key) != selected_road
if road_changed:
    st.session_state[road_changed_key] = selected_road

if sim_mode == "Manual Scenario Injection":
    st.sidebar.markdown("#### Scenario Parameters")
    man_vehicles = st.sidebar.slider("Current Road Lane Vehicle Count (cars on lane)", 10, 150, 85)

    man_speed = st.sidebar.slider("Average Speed (km/h)", 10, 80, 25)
    man_weather = st.sidebar.selectbox("Weather Condition", ["Clear", "Rain", "Fog", "Storm"])
    man_accident = st.sidebar.checkbox("⚠️ Flag Accident Event", value=False)
    man_emergency = st.sidebar.checkbox("🚨 Emergency Preemption Mode", value=True)
    man_emerg_type = st.sidebar.selectbox("Emergency Vehicle Type", ["Ambulance", "Fire Truck", "Police Vehicle"]) if man_emergency else None

    if st.sidebar.button("⚡ Inject Custom Telemetry Frame", use_container_width=True):
        custom_input = {
            "road": selected_road,
            "vehicle_count": man_vehicles,
            "average_speed": float(man_speed),
            "road_occupancy_pct": round(min(100.0, (man_vehicles / 120.0) * 100.0), 1),
            "accident": man_accident,
            "emergency_vehicle": man_emergency,
            "emergency_type": man_emerg_type,
            "weather": man_weather
        }
        with st.spinner(f"Executing CrewAI agent pipeline for {selected_road}..."):
            st.session_state[road_telemetry_key] = custom_input
            st.session_state[road_report_key] = run_traffic_crew(custom_input, registered_phone=reg_phone)
            st.sidebar.success(f"Custom telemetry frame processed for {selected_road}")
            st.rerun()
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### 🚨 Quick Emergency Scenario Triggers")
    if st.button("🚨 ACTIVATE GREEN CORRIDOR ALERT", use_container_width=True):
        sim_data = {
            "road": selected_road,
            "vehicle_count": 150,
            "average_speed": 12.0,
            "accident": True,
            "emergency_vehicle": True,
            "emergency_type": "Ambulance",
            "manual_green_corridor": True
        }
        st.session_state[road_telemetry_key] = sim_data
        st.session_state[road_report_key] = run_traffic_crew(sim_data, registered_phone=reg_phone)
        st.rerun()
    col_sc1, col_sc2 = st.sidebar.columns(2)
    with col_sc1:
        if st.button("🔴 Accident", use_container_width=True):
            sim_data = {
                "road": selected_road,
                "vehicle_count": 80,
                "average_speed": 22.0,
                "accident": True,
                "accident_status": True,
                "emergency_vehicle": False
            }
            st.session_state[road_telemetry_key] = sim_data
            st.session_state[road_report_key] = run_traffic_crew(sim_data, registered_phone=reg_phone)
            st.rerun()
        if st.button("🚑 Ambulance", use_container_width=True):
            sim_data = {
                "road": selected_road,
                "vehicle_count": 160,
                "average_speed": 14.0,
                "accident": True,
                "emergency_vehicle": True,
                "emergency_type": "Ambulance"
            }
            st.session_state[road_telemetry_key] = sim_data
            st.session_state[road_report_key] = run_traffic_crew(sim_data, registered_phone=reg_phone)
            st.rerun()
    with col_sc2:
        if st.button("🚒 Fire Truck", use_container_width=True):
            sim_data = {
                "road": selected_road,
                "vehicle_count": 140,
                "average_speed": 18.0,
                "accident": True,
                "emergency_vehicle": True,
                "emergency_type": "Fire Truck"
            }
            st.session_state[road_telemetry_key] = sim_data
            st.session_state[road_report_key] = run_traffic_crew(sim_data, registered_phone=reg_phone)
            st.rerun()
        if st.button("✅ Resolve All", use_container_width=True):
            sim_data = {
                "road": selected_road,
                "vehicle_count": 45,
                "average_speed": 50.0,
                "accident": False,
                "emergency_vehicle": False,
                "accident_resolved": True,
                "emergency_vehicle_passed": True
            }
            st.session_state[road_telemetry_key] = sim_data
            st.session_state[road_report_key] = run_traffic_crew(sim_data, registered_phone=reg_phone)
            st.rerun()

else:
    st.sidebar.caption("🌐 Currently pulling live real-time weather & traffic telemetry via Open-Meteo API & OpenStreetMap GPS coordinates.")
    if st.sidebar.button("⚡ Fetch Live Real-Time API Feed & Run Agents", use_container_width=True):
        with st.spinner("Fetching Live API data & executing CrewAI Multi-Agent Pipeline..."):
            sim_data = TrafficDataFetcher.get_traffic_data(selected_road)
            st.session_state[road_telemetry_key] = sim_data
            st.session_state[road_report_key] = run_traffic_crew(sim_data, registered_phone=reg_phone)
            st.sidebar.success(f"Live API data fetched for {selected_road}!")
            st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔊 System Controls")

enable_voice = st.sidebar.toggle("Enable Audio Alerts", value=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📄 Reporting")
pdf_bytes_sb = generate_traffic_pdf_report(
    road_name=selected_road,
    reports=get_latest_reports(limit=20),
    analytics=get_analytics_summary(limit=20),
    alerts=get_active_alerts(limit=20)
)
st.sidebar.download_button(
    label="📥 Export Executive PDF Report",
    data=pdf_bytes_sb,
    file_name=f"Traffic_Executive_Report_{selected_road.replace(' ', '_')}.pdf",
    mime="application/pdf",
    use_container_width=True
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🟢 Agent Service Status")
st.sidebar.markdown("""
- 🟢 **Traffic Monitor Agent**: Active
- 🟢 **Driver Behavior & Safety Agent**: Active
- 🟢 **Congestion Prediction Agent**: Active
- 🟢 **Emergency Vehicle Agent**: Active
- 🟢 **Signal Optimization Agent**: Active
- 🟢 **Citizen Liaison Agent**: Active
- 🟢 **Analytics Agent**: Active
""")

# Check if we need to fetch new telemetry frame (only on manual refresh, road change, or initial load)
needs_fetch = refresh_requested or road_changed or (road_telemetry_key not in st.session_state) or (road_report_key not in st.session_state)

if needs_fetch:
    prev_state = st.session_state.get(session_key)
    current_telemetry = TrafficDataFetcher.get_traffic_data(selected_road)
    full_report = run_traffic_crew(current_telemetry, registered_phone=reg_phone)

    if prev_state:
        delta_vc = current_telemetry.get("vehicle_count", 0) - prev_state.get("vehicle_count", 0)
        delta_spd = round(current_telemetry.get("average_speed", 0.0) - prev_state.get("average_speed", 0.0), 1)
        delta_cg = current_telemetry.get("congestion_level", 0) - prev_state.get("congestion_level", 0)
        data_changed = (delta_vc != 0 or delta_spd != 0.0 or delta_cg != 0)
    else:
        delta_vc, delta_spd, delta_cg = 0, 0.0, 0
        data_changed = True

    st.session_state[road_telemetry_key] = current_telemetry
    st.session_state[road_report_key] = full_report
    st.session_state[session_key] = current_telemetry
    st.session_state[f"deltas_{selected_road}"] = (delta_vc, delta_spd, delta_cg)
    st.session_state[f"changed_{selected_road}"] = data_changed
else:
    current_telemetry = st.session_state[road_telemetry_key]
    full_report = st.session_state[road_report_key]
    prev_state = st.session_state.get(session_key)
    delta_vc, delta_spd, delta_cg = st.session_state.get(f"deltas_{selected_road}", (0, 0.0, 0))
    data_changed = st.session_state.get(f"changed_{selected_road}", False)



# Save current telemetry in session state for next cycle comparison
st.session_state[session_key] = current_telemetry

t_rep = full_report.get("traffic_report") or {}
d_safe = full_report.get("driver_safety") or {}
c_pred = full_report.get("congestion_prediction") or {}
e_corr = full_report.get("emergency_corridor") or {}
s_opt = full_report.get("signal_optimization") or {}
c_alt = full_report.get("citizen_alerts") or {}
a_sum = full_report.get("analytics_summary") or {}

# Extract guaranteed non-null metric values
vehicles_val = current_telemetry.get("vehicle_count", 50)
density_val = current_telemetry.get("traffic_density", "MEDIUM").title()
speed_val = current_telemetry.get("average_speed", 40.0)
c_score_val = current_telemetry.get("congestion_level", 40)
g_time_val = s_opt.get("recommended_green_time_sec") if s_opt.get("recommended_green_time_sec") is not None else 30

# Render Previous vs Current Telemetry Comparison Badge
vc_str = f"+{delta_vc}" if delta_vc > 0 else (f"{delta_vc}" if delta_vc < 0 else "0")
spd_str = f"+{delta_spd}" if delta_spd > 0 else (f"{delta_spd}" if delta_spd < 0 else "0")
cg_str = f"+{delta_cg}%" if delta_cg > 0 else (f"{delta_cg}%" if delta_cg < 0 else "0%")

st.markdown(
    f"""
    <div style="background-color: #0F172A; border: 1px solid #334155; border-radius: 12px; padding: 1rem 1.4rem; margin-bottom: 1.2rem; box-shadow: 0 4px 20px rgba(0,0,0,0.2);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
            <div>
                <span style="background-color: #0284C7; color: white; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 0.78rem;">📡 {current_telemetry.get('data_mode', 'LIVE TELEMETRY')}</span>
                <span style="color: #94A3B8; font-weight: 600; font-size: 0.85rem; margin-left: 10px;">⏱️ Last Updated: <b style="color: #38BDF8;">{current_telemetry.get('time_display', 'Just now')}</b></span>
            </div>
            <div style="display: flex; gap: 18px; font-size: 0.88rem; font-weight: 600; color: #E2E8F0;">
                <div>🚗 Vehicle Delta: <b style="color: {'#34D399' if delta_vc <= 0 else '#F87171'};">{vc_str}</b></div>
                <div>⚡ Velocity Delta: <b style="color: {'#34D399' if delta_spd >= 0 else '#F87171'};">{spd_str} km/h</b></div>
                <div>📈 Congestion Delta: <b style="color: {'#34D399' if delta_cg <= 0 else '#F87171'};">{cg_str}</b></div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# Emergency Alert Banners & Audio Announcements
if e_corr.get("green_corridor_active"):
    emerg_type = e_corr.get('vehicle_type', 'Emergency Vehicle')
    affected_lane = e_corr.get('affected_lane', 'Lane 1')
    alert_title = f"🚨 EMERGENCY {emerg_type.upper()} GREEN CORRIDOR ACTIVE"
    alert_msg = e_corr.get("voice_script") or f"Emergency alert. A {emerg_type} is approaching on {affected_lane} of {selected_road}. All intersection signals locked green!"
    
    st.markdown(
        f"""
        <div class='banner-critical'>
            <b>🚨 EMERGENCY GREEN CORRIDOR ACTIVE:</b> Priority override locked for <b>{emerg_type}</b> on <b>{affected_lane}</b> of <b>{selected_road}</b>. Intersections cleared.
        </div>
        """,
        unsafe_allow_html=True
    )
    
    voice_html = generate_voice_announcement_html(alert_title, alert_msg, enabled=enable_voice)
    if voice_html:
        st.components.v1.html(voice_html, height=0)

elif t_rep.get("accident"):
    alert_title = "⚠️ TRAFFIC ACCIDENT DETECTED"
    detour_road = c_pred.get('recommended_alternate_roads', ['Service Lane'])[0]
    alert_msg = e_corr.get("voice_script") or f"Accident reported on {selected_road}. Rerouting traffic via {detour_road}."
    
    st.markdown(
        f"""
        <div class='banner-warning'>
            <b>⚠️ TRAFFIC INCIDENT REPORTED:</b> Collision event on <b>{selected_road}</b>. Traffic rerouted via {detour_road}.
        </div>
        """,
        unsafe_allow_html=True
    )
    
    voice_html = generate_voice_announcement_html(alert_title, alert_msg, enabled=enable_voice)
    if voice_html:
        st.components.v1.html(voice_html, height=0)


# ⚡ AUTOMATIC AI CONDITION-TRIGGERED DISPATCH NOTIFICATION BANNER
auto_status = full_report.get("auto_dispatch_status", {})
if auto_status.get("triggered"):
    recipient_num = auto_status.get('recipient', '+916383258373')
    clean_num = "".join(filter(str.isdigit, recipient_num))
    
    # Prepare URL encoded message for WhatsApp chat launch
    wa_payload = auto_status.get("whatsapp_response", {}).get("payload", f"TRAFFIC ALERT for {selected_road}")
    import urllib.parse
    encoded_text = urllib.parse.quote(wa_payload)
    wa_direct_link = f"https://wa.me/{clean_num}?text={encoded_text}"
    
    st.markdown(
        f"""
        <div style="background-color: #ECFDF5; border: 1px solid #A7F3D0; color: #065F46 !important; padding: 1rem 1.2rem; border-radius: 10px; font-weight: 600; margin-bottom: 1.2rem; font-size: 0.92rem; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
            <div>
                🤖 <b>AUTOMATIC AI DISPATCH TRIGGERED:</b> {auto_status.get('reason')}<br>
                <span style="font-weight: normal; font-size: 0.82rem; color: #047857 !important;">Alert generated for registered phone: <b>{recipient_num}</b></span>
            </div>
            <a href="{wa_direct_link}" target="_blank" style="text-decoration: none;">
                <div style="background-color: #25D366; color: white !important; font-weight: 700; padding: 8px 16px; border-radius: 6px; font-size: 13px; box-shadow: 0 4px 10px rgba(37,211,102,0.3);">
                    📲 Send Real WhatsApp Message to {recipient_num}
                </div>
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )

# Executive White Metric Grid
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(
        f"""
        <div class='metric-box'>
            <div class='metric-head'>Current Road Lane Vehicle Count</div>
            <div class='metric-body'>{vehicles_val}</div>
            <div class='metric-sub'>vehicles on lane</div>
        </div>

        """,
        unsafe_allow_html=True
    )

with col2:
    d_color = "#059669" if density_val == "Low" else ("#D97706" if density_val == "Medium" else "#DC2626")
    st.markdown(
        f"""
        <div class='metric-box' style='border-left: 4px solid {d_color};'>
            <div class='metric-head'>Traffic Density</div>
            <div class='metric-body' style='color: {d_color};'>{density_val}</div>
            <div class='metric-sub'>Capacity Index</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        f"""
        <div class='metric-box'>
            <div class='metric-head'>Average Velocity</div>
            <div class='metric-body'>{speed_val}</div>
            <div class='metric-sub'>km / hour</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col4:
    st.markdown(
        f"""
        <div class='metric-box'>
            <div class='metric-head'>Congestion Index</div>
            <div class='metric-body' style='color: #DB2777;'>{c_score_val}</div>
            <div class='metric-sub'>scale 0 to 100</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col5:
    st.markdown(
        f"""
        <div class='metric-box'>
            <div class='metric-head'>Green Phase Target</div>
            <div class='metric-body' style='color: #2563EB;'>{g_time_val}</div>
            <div class='metric-sub'>seconds duration</div>
        </div>
        """,
        unsafe_allow_html=True
    )


st.markdown("<br>", unsafe_allow_html=True)

# Main Navigation Tabs
tab1, tab_scen, tab_alloc, tab_flood, tab_driver, tab_gis, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Executive Operations & Agent Flow", 
    "🤖 AI Scenario Simulator",
    "🏥 Emergency Resource Allocation",
    "🌊 Flood & Waterlogging Intelligence",
    "🛡️ Driver Safety Analytics",
    "🗺️ GIS Map & Google Satellite", 
    "🚦 Signal Controllers & Preemption", 
    "📢 Citizen Broadcast Feed", 
    "📈 Analytics & Sustainability",
    "🛡️ V2I Pre-Crash Safety"
])

# Extract new agent data
v2i = full_report.get("v2i_precrash", {})
sc_sim = full_report.get("scenario_simulation", {})
em_res = full_report.get("emergency_resource", {})
fl_trf = full_report.get("flood_traffic", {})


with tab1:
    st.markdown("#### 🤖 CrewAI Multi-Agent Execution Trace")
    st.caption("Real-time decision pipeline across 10 specialized autonomous agents")

    ag1, ag2 = st.columns(2)
    with ag1:
        st.markdown(
            f"""
            <div class='agent-row-card'>
                <div class='agent-title-text'>1. Traffic Monitoring Agent</div>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Target Road:</b> {t_rep.get('road')}</p>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Weather Factor:</b> {t_rep.get('weather')}</p>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Incident Status:</b> {'Accident Flagged ⚠️' if t_rep.get('accident') else 'Normal 🟢'}</p>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Emergency Ingestion:</b> {'Detected 🚨' if t_rep.get('emergency_vehicle') else 'None'}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class='agent-row-card'>
                <div class='agent-title-text' style='color: #E11D48;'>2. Driver Behavior & Safety Agent</div>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Safety Score:</b> <b style='color: {'#059669' if d_safe.get('safety_score', 100) >= 80 else ('#D97706' if d_safe.get('safety_score', 100) >= 60 else '#DC2626')};'>{d_safe.get('safety_score', 100)} / 100</b></p>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Risk Level:</b> <span style='color: {'#DC2626' if d_safe.get('risk_level') in ['HIGH', 'CRITICAL'] else '#059669'}; font-weight: 700;'>{d_safe.get('risk_level', 'LOW')}</span></p>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Total Infractions:</b> {d_safe.get('total_violations', 0)} detected</p>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Primary Hazard:</b> {d_safe.get('primary_hazard', 'None')}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class='agent-row-card'>
                <div class='agent-title-text' style='color: #0284C7;'>3. Flood & Waterlogging Agent</div>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Flood Risk Score:</b> <b style='color: {'#34D399' if fl_trf.get('flood_risk_score', 0) < 40 else ('#FBBF24' if fl_trf.get('flood_risk_score', 0) < 70 else '#F87171')};'>{fl_trf.get('flood_risk_score', 15)} / 100</b></p>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Road Safety Status:</b> <b style='color: #0EA5E9;'>{fl_trf.get('road_status', 'SAFE')}</b></p>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Rainfall:</b> {fl_trf.get('rainfall_mm_per_hour', 0.0)} mm/hr</p>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>ETA Waterlogging:</b> {fl_trf.get('estimated_time_to_waterlogging', 'None')}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class='agent-row-card'>
                <div class='agent-title-text' style='color: #0284C7;'>4. Emergency Resource Allocation Agent</div>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Selected Ambulance:</b> <b style='color: #38BDF8;'>{em_res.get('selected_ambulance', {}).get('ambulance_id', 'AMB001')}</b> ({em_res.get('selected_ambulance', {}).get('response_time_minutes', 6)} min ETA)</p>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Selected Hospital:</b> <b style='color: #34D399;'>{em_res.get('selected_hospital', {}).get('hospital_name', 'City Emergency Hospital')}</b></p>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Total Response Time:</b> <b style='color: #FBBF24;'>{em_res.get('total_estimated_time', 15)} mins</b></p>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Allocation Score:</b> {em_res.get('decision_score', 94.0)} / 100</p>
            </div>
            """,
            unsafe_allow_html=True
        )


        st.markdown(
            f"""
            <div class='agent-row-card'>
                <div class='agent-title-text' style='color: #DC2626;'>5. Emergency Vehicle Agent</div>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Priority Level:</b> {e_corr.get('priority_level')}</p>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Green Corridor:</b> {'ACTIVE 🚨' if e_corr.get('green_corridor_active') else 'INACTIVE 🟢'}</p>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Cleared Corridor:</b> {', '.join(e_corr.get('corridor_route', [])) or 'Standard'}</p>
            </div>
            """,
            unsafe_allow_html=True
        )


        st.markdown(
            f"""
            <div class='agent-row-card'>
                <div class='agent-title-text' style='color: #059669;'>6. Citizen Communication Agent</div>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Broadcast Title:</b> {c_alt.get('title')}</p>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Severity Tier:</b> {c_alt.get('severity')}</p>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Reroute Guidance:</b> {c_alt.get('alternate_route') or 'None required'}</p>
            </div>
            """,
            unsafe_allow_html=True
        )


    with ag2:
        st.markdown(
            f"""
            <div class='agent-row-card'>
                <div class='agent-title-text' style='color: #D97706;'>2. Congestion Prediction Agent</div>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Congestion Risk Tier:</b> {c_pred.get('risk_level')}</p>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>30-Min Projection:</b> {c_pred.get('predicted_trend')}</p>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Estimated Delay:</b> {c_pred.get('estimated_delay_minutes')} mins</p>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Bypass Alternatives:</b> {', '.join(c_pred.get('recommended_alternate_roads', []))}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class='agent-row-card'>
                <div class='agent-title-text' style='color: #7C3AED;'>4. Signal Optimization Agent</div>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Control Mode:</b> {s_opt.get('signal_mode')}</p>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Base Cycle:</b> {s_opt.get('current_green_time_sec')} sec</p>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Dynamic Phase Split:</b> +{s_opt.get('dynamic_increase_sec')} sec</p>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Delay Reduction:</b> {s_opt.get('estimated_wait_time_reduction_pct')}%</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class='agent-row-card'>
                <div class='agent-title-text' style='color: #0284C7;'>6. Analytics Agent</div>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Road Performance Score:</b> {a_sum.get('road_performance_score')} / 100</p>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Estimated Carbon Footprint:</b> {a_sum.get('carbon_emission_kg')} kg CO₂</p>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Summary Note:</b> {a_sum.get('key_insights', ['Normal operations'])[0]}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class='agent-row-card'>
                <div class='agent-title-text' style='color: #6366F1;'>7. Scenario Simulation & Decision Agent</div>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Winning Strategy:</b> {sc_sim.get('winning_scenario_id', 'SCEN-C')}</p>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Decision Score:</b> {sc_sim.get('decision_score', 91.5)} / 100</p>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Predicted Congestion:</b> {sc_sim.get('expected_congestion', 38)}%</p>
                <p style='margin:4px 0; font-size: 0.88rem; color: #334155;'><b>Predicted Response:</b> {sc_sim.get('emergency_response_time', 4)} mins</p>
            </div>
            """,
            unsafe_allow_html=True
        )


with tab_scen:
    st.markdown("#### 🤖 AI Scenario Simulator & Decision Intelligence Layer")
    st.caption("Proactively evaluates candidate actions ('What happens if I take this action?'), simulates multi-metric physics/queue outcomes, and scores strategies before signal execution.")

    scen_data = full_report.get("scenario_simulation") or {}
    win_action = scen_data.get("recommended_action", "Maintain standard 30s adaptive timing schedule")
    win_score = scen_data.get("decision_score", 76.5)
    win_cong = scen_data.get("expected_congestion", 38)
    win_delay = scen_data.get("expected_delay", 6)
    win_emerg = scen_data.get("emergency_response_time", 4)
    win_carbon = scen_data.get("expected_carbon_emission", "LOW")
    win_reason = scen_data.get("reason", "This strategy minimizes congestion and emergency response time while reducing carbon emissions.")

    # 1. 🏆 AI RECOMMENDED ACTION BANNER
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 100%); border: 2px solid #6366F1; border-radius: 12px; padding: 1.4rem; margin-bottom: 1.4rem; color: white;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; margin-bottom: 10px;">
                <div>
                    <span style="background: #6366F1; color: white; padding: 4px 12px; border-radius: 6px; font-weight: 800; font-size: 0.82rem;">🏆 AI RECOMMENDED ACTION</span>
                    <h3 style="margin: 8px 0 2px 0; color: #38BDF8; font-size: 1.25rem;">{win_action}</h3>
                </div>
                <div style="text-align: right; background: #312E81; padding: 8px 16px; border-radius: 8px; border: 1px solid #818CF8;">
                    <div style="font-size: 0.75rem; color: #A5B4FC; font-weight: 600;">DECISION SCORE</div>
                    <div style="font-size: 1.6rem; font-weight: 900; color: #34D399;">{win_score}<span style="font-size: 0.9rem; color: #94A3B8;">/100</span></div>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; font-size: 0.85rem; margin-top: 12px;">
                <div style="background: #1E293B; padding: 10px; border-radius: 8px;"><b>Expected Congestion:</b> <b style="color: #34D399;">{win_cong}%</b></div>
                <div style="background: #1E293B; padding: 10px; border-radius: 8px;"><b>Expected Delay:</b> <b style="color: #38BDF8;">{win_delay} min</b></div>
                <div style="background: #1E293B; padding: 10px; border-radius: 8px;"><b>Emergency Response:</b> <b style="color: #FBBF24;">{win_emerg} min</b></div>
                <div style="background: #1E293B; padding: 10px; border-radius: 8px;"><b>CO₂ Impact:</b> <b style="color: {'#34D399' if win_carbon == 'LOW' else '#F87171'};">{win_carbon}</b></div>
            </div>
            <div style="margin-top: 12px; font-size: 0.85rem; color: #CBD5E1; background: #0F172A; padding: 10px 14px; border-radius: 6px; border-left: 4px solid #34D399;">
                <b>🧠 AI Decision Explanation:</b> {win_reason}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 2. BEFORE VS AFTER COMPARISON GRID
    st.markdown("##### ⚡ BEFORE VS AFTER AI DECISION COMPARISON")
    actual_b = scen_data.get("actual_baseline", {"congestion": 82, "delay": 18, "emergency_response": 14, "carbon": "HIGH"})
    after_p = scen_data.get("after_predicted", {"congestion": 38, "delay": 6, "emergency_response": 4, "carbon": "LOW"})

    col_ba1, col_ba2 = st.columns(2)
    with col_ba1:
        st.markdown(
            f"""
            <div style="background: #0F172A; border: 1px solid #EF4444; border-radius: 10px; padding: 1rem; color: white;">
                <div style="font-weight: 700; color: #F87171; font-size: 0.95rem; margin-bottom: 8px;">🔴 CURRENT / ACTUAL BASELINE</div>
                <div style="font-size: 0.85rem; line-height: 1.6;">
                    <div><b>Congestion Level:</b> <span style="color: #F87171; font-weight: 700;">{actual_b.get('congestion')}%</span></div>
                    <div><b>Travel Delay:</b> {actual_b.get('delay')} minutes</div>
                    <div><b>Emergency Response Time:</b> {actual_b.get('emergency_response')} minutes</div>
                    <div><b>Carbon Emission:</b> <span style="color: #F87171;">{actual_b.get('carbon')}</span></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_ba2:
        st.markdown(
            f"""
            <div style="background: #0F172A; border: 1px solid #34D399; border-radius: 10px; padding: 1rem; color: white;">
                <div style="font-weight: 700; color: #34D399; font-size: 0.95rem; margin-bottom: 8px;">🟢 AFTER AI DECISION (PREDICTED)</div>
                <div style="font-size: 0.85rem; line-height: 1.6;">
                    <div><b>Predicted Congestion:</b> <span style="color: #34D399; font-weight: 700;">{after_p.get('congestion')}%</span></div>
                    <div><b>Expected Delay:</b> {after_p.get('delay')} minutes</div>
                    <div><b>Expected Emergency Response:</b> {after_p.get('emergency_response')} minutes</div>
                    <div><b>Predicted Carbon Output:</b> <span style="color: #34D399;">{after_p.get('carbon')}</span></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 3. EVALUATED SCENARIOS GRID
    st.markdown("<br>##### 🔬 CANDIDATE SCENARIOS EVALUATED & RANKED", unsafe_allow_html=True)
    eval_scens = scen_data.get("scenarios_evaluated", [
        {"scenario_id": "SCEN-A", "name": "Scenario A: Maintain Current Timing", "action": "Maintain 30s timing", "predicted_congestion": 82, "predicted_delay": 18, "predicted_emergency_time": 14, "predicted_carbon": "HIGH", "decision_score": 42.0, "selected": False},
        {"scenario_id": "SCEN-B", "name": "Scenario B: Extended Green Phase (+25s)", "action": "Extend green signal to 55s", "predicted_congestion": 62, "predicted_delay": 11, "predicted_emergency_time": 8, "predicted_carbon": "MEDIUM", "decision_score": 76.0, "selected": False},
        {"scenario_id": "SCEN-C", "name": "Scenario C: Emergency Green Corridor", "action": "Activate Green Corridor (90s lock)", "predicted_congestion": 38, "predicted_delay": 6, "predicted_emergency_time": 4, "predicted_carbon": "LOW", "decision_score": 91.5, "selected": True}
    ])

    scen_cols = st.columns(len(eval_scens))
    for idx, sc_item in enumerate(eval_scens):
        with scen_cols[idx]:
            is_win = sc_item.get("selected", False)
            card_b = "#34D399" if is_win else "#334155"
            badge = "🏆 WINNER" if is_win else f"RANK #{idx+1}"
            badge_color = "#34D399" if is_win else "#94A3B8"

            st.markdown(
                f"""
                <div style="background: #0F172A; border: 2px solid {card_b}; border-radius: 8px; padding: 12px; color: white; height: 100%;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-weight: 700; font-size: 0.8rem; color: #38BDF8;">{sc_item.get('scenario_id')}</span>
                        <span style="font-weight: 800; font-size: 0.75rem; color: {badge_color}; background: #1E293B; padding: 2px 6px; border-radius: 4px;">{badge}</span>
                    </div>
                    <div style="font-weight: 700; font-size: 0.88rem; color: #E2E8F0; margin-bottom: 6px;">{sc_item.get('name')}</div>
                    <div style="font-size: 1.3rem; font-weight: 800; color: {'#34D399' if is_win else '#FBBF24'}; margin-bottom: 8px;">Score: {sc_item.get('decision_score')}/100</div>
                    <div style="font-size: 0.78rem; color: #94A3B8; line-height: 1.5;">
                        <div>• Congestion: <b>{sc_item.get('predicted_congestion')}%</b></div>
                        <div>• Delay: <b>{sc_item.get('predicted_delay')} min</b></div>
                        <div>• Emerg. Time: <b>{sc_item.get('predicted_emergency_time')} min</b></div>
                        <div>• CO₂: <b>{sc_item.get('predicted_carbon')}</b></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    # 4. INNOVATIVE WHAT-IF ANALYSIS INTERACTIVE SANDBOX
    st.markdown("<br>##### 🧪 INNOVATIVE WHAT-IF ANALYSIS INTERACTIVE SANDBOX", unsafe_allow_html=True)
    st.caption("Adjust parameters below to evaluate real-time AI predictions: 'What happens if this value changes?'")

    wcol1, wcol2, wcol3 = st.columns(3)
    with wcol1:
        sandbox_g_time = st.slider("Green Signal Duration (sec)", min_value=10, max_value=120, value=50, step=5)
        sandbox_veh = st.slider("Current Road Lane Vehicle Count", min_value=10, max_value=250, value=int(current_telemetry.get("vehicle_count", 90)), step=10)

    with wcol2:
        sandbox_emerg = st.selectbox("Emergency Vehicle Status", ["None", "Ambulance (Medical Emergency)", "Fire Truck (Fire Response)", "Police Vehicle (Pursuit)"])
        sandbox_acc = st.checkbox("Accident Reported on Lane", value=bool(current_telemetry.get("accident", False)))
    with wcol3:
        sandbox_weather = st.selectbox("Weather Condition", ["CLEAR", "RAIN", "FOG", "STORM"])
        sandbox_reroute = st.checkbox("Enable Alternate Route Diversion", value=False)

    sb_input = {
        "road": selected_road,
        "vehicle_count": sandbox_veh,
        "average_speed": max(10.0, 60.0 - (sandbox_veh * 0.2)),
        "congestion_level": min(100, int((sandbox_veh / 180.0) * 100)),
        "accident": sandbox_acc,
        "emergency_vehicle": (sandbox_emerg != "None"),
        "emergency_type": sandbox_emerg.split()[0] if sandbox_emerg != "None" else "NONE",
        "weather": sandbox_weather
    }

    from tools.scenario_simulation_tools import ScenarioSimulator
    sb_res = ScenarioSimulator.simulate_scenarios(sb_input)
    sb_win = sb_res.get("after_predicted", {})

    st.markdown(
        f"""
        <div style="background: #0F172A; border: 2px dashed #38BDF8; border-radius: 10px; padding: 1.2rem; margin-top: 1rem; color: white;">
            <div style="font-weight: 700; color: #38BDF8; font-size: 1rem; margin-bottom: 8px;">🔮 WHAT-IF PREDICTION OUTCOME</div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 10px; font-size: 0.88rem;">
                <div style="background: #1E293B; padding: 10px; border-radius: 6px;"><b>Predicted Congestion:</b> <b style="color: #34D399;">{sb_win.get('congestion')}%</b></div>
                <div style="background: #1E293B; padding: 10px; border-radius: 6px;"><b>Expected Delay:</b> <b style="color: #38BDF8;">{sb_win.get('delay')} min</b></div>
                <div style="background: #1E293B; padding: 10px; border-radius: 6px;"><b>Emergency Response:</b> <b style="color: #FBBF24;">{sb_win.get('emergency_response')} min</b></div>
                <div style="background: #1E293B; padding: 10px; border-radius: 6px;"><b>Predicted CO₂ Impact:</b> <b style="color: #34D399;">{sb_win.get('carbon')}</b></div>
                <div style="background: #1E293B; padding: 10px; border-radius: 6px;"><b>Simulated Decision Score:</b> <b style="color: #34D399;">{sb_res.get('decision_score')}/100</b></div>
            </div>
            <div style="margin-top: 8px; font-size: 0.82rem; color: #94A3B8;"><b>Recommended Strategy:</b> {sb_res.get('recommended_action')}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with tab_alloc:
    st.markdown("#### 🏥 Emergency Resource Allocation Agent")
    st.caption("Intelligently evaluates available fleet ambulances and nearby regional medical centers, scoring multi-attribute suitability (travel time, traffic, medical capabilities, ICU beds, trauma center status) to minimize emergency response times.")

    alloc_data = full_report.get("emergency_resource") or {}
    sel_amb = alloc_data.get("selected_ambulance", {"ambulance_id": "AMB001", "capability": "ADVANCED LIFE SUPPORT", "response_time_minutes": 6, "distance_km": 2.4, "score": 91.0})
    sel_hosp = alloc_data.get("selected_hospital", {"hospital_id": "H002", "hospital_name": "City Emergency Hospital", "travel_time_minutes": 9, "icu_available": True, "trauma_center": True, "beds_available": 8, "score": 94.0})

    # 1. 🏆 AI RESOURCE ALLOCATION BANNER
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #0F172A 0%, #065F46 100%); border: 2px solid #10B981; border-radius: 12px; padding: 1.4rem; margin-bottom: 1.4rem; color: white;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; margin-bottom: 10px;">
                <div>
                    <span style="background: #10B981; color: white; padding: 4px 12px; border-radius: 6px; font-weight: 800; font-size: 0.82rem;">🏆 AI RECOMMENDED EMERGENCY ALLOCATION</span>
                    <h3 style="margin: 8px 0 2px 0; color: #34D399; font-size: 1.25rem;">Dispatch {sel_amb.get('ambulance_id')} → Route to {sel_hosp.get('hospital_name')}</h3>
                </div>
                <div style="text-align: right; background: #064E3B; padding: 8px 16px; border-radius: 8px; border: 1px solid #34D399;">
                    <div style="font-size: 0.75rem; color: #A7F3D0; font-weight: 600;">ALLOCATION SCORE</div>
                    <div style="font-size: 1.6rem; font-weight: 900; color: #34D399;">{alloc_data.get('decision_score', 94.0)}<span style="font-size: 0.9rem; color: #94A3B8;">/100</span></div>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; font-size: 0.85rem; margin-top: 12px;">
                <div style="background: #1E293B; padding: 10px; border-radius: 8px;"><b>Ambulance ETA:</b> <b style="color: #38BDF8;">{sel_amb.get('response_time_minutes', 6)} mins</b></div>
                <div style="background: #1E293B; padding: 10px; border-radius: 8px;"><b>Hospital ETA:</b> <b style="color: #FBBF24;">{sel_hosp.get('travel_time_minutes', 9)} mins</b></div>
                <div style="background: #1E293B; padding: 10px; border-radius: 8px;"><b>Total Response Time:</b> <b style="color: #34D399;">{alloc_data.get('total_estimated_time', 15)} mins</b></div>
                <div style="background: #1E293B; padding: 10px; border-radius: 8px;"><b>Green Corridor:</b> <b style="color: #34D399;">ACTIVE 🚨</b></div>
            </div>
            <div style="margin-top: 12px; font-size: 0.85rem; color: #CBD5E1; background: #0F172A; padding: 10px 14px; border-radius: 6px; border-left: 4px solid #34D399;">
                <b>🧠 AI Allocation Explanation:</b> {alloc_data.get('reason', 'Optimal pairing selected based on response time, medical capability, and ICU availability.')}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 2. SELECTED AMBULANCE & HOSPITAL CARDS SIDE BY SIDE
    acol1, acol2 = st.columns(2)
    with acol1:
        st.markdown(
            f"""
            <div style="background: #0F172A; border: 1px solid #38BDF8; border-radius: 10px; padding: 1rem; color: white;">
                <div style="font-weight: 700; color: #38BDF8; font-size: 0.98rem; margin-bottom: 8px;">🚑 SELECTED AMBULANCE DETAILS</div>
                <div style="font-size: 0.88rem; line-height: 1.6;">
                    <div><b>Ambulance ID:</b> <span style="color: #38BDF8; font-weight: 800;">{sel_amb.get('ambulance_id')}</span></div>
                    <div><b>Medical Capability:</b> {sel_amb.get('capability', 'ADVANCED LIFE SUPPORT')}</div>
                    <div><b>Distance to Incident:</b> {sel_amb.get('distance_km', 2.4)} km</div>
                    <div><b>Estimated Arrival (ETA):</b> <span style="color: #34D399; font-weight: 700;">{sel_amb.get('response_time_minutes')} minutes</span></div>
                    <div><b>Status:</b> <span style="color: #34D399; font-weight: 700;">EN ROUTE TO ACCIDENT</span></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with acol2:
        st.markdown(
            f"""
            <div style="background: #0F172A; border: 1px solid #34D399; border-radius: 10px; padding: 1rem; color: white;">
                <div style="font-weight: 700; color: #34D399; font-size: 0.98rem; margin-bottom: 8px;">🏥 SELECTED HOSPITAL DETAILS</div>
                <div style="font-size: 0.88rem; line-height: 1.6;">
                    <div><b>Hospital Name:</b> <span style="color: #34D399; font-weight: 800;">{sel_hosp.get('hospital_name')}</span></div>
                    <div><b>ICU Bed Availability:</b> <span style="color: {'#34D399' if sel_hosp.get('icu_available') else '#F87171'}; font-weight: 700;">{'YES (AVAILABLE)' if sel_hosp.get('icu_available') else 'NO'}</span></div>
                    <div><b>Trauma Center:</b> {'YES (Level 1 Trauma)' if sel_hosp.get('trauma_center') else 'NO'}</div>
                    <div><b>Hospital Travel Time:</b> <span style="color: #FBBF24; font-weight: 700;">{sel_hosp.get('travel_time_minutes')} minutes</span></div>
                    <div><b>Beds Available:</b> {sel_hosp.get('beds_available', 8)} emergency beds</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 3. AMBULANCE & HOSPITAL COMPARISON TABLES
    st.markdown("<br>##### 📊 AI AMBULANCE & HOSPITAL SUITABILITY COMPARISON TABLES", unsafe_allow_html=True)
    
    col_tbl1, col_tbl2 = st.columns(2)
    with col_tbl1:
        st.markdown("###### 🚑 Ambulance Fleet Evaluation")
        amb_opts = alloc_data.get("ambulance_options", [
            {"ambulance_id": "AMB001", "eta_minutes": 6, "capability_rating": "HIGH", "traffic_density": "MEDIUM", "score": 91.0},
            {"ambulance_id": "AMB002", "eta_minutes": 4, "capability_rating": "LOW", "traffic_density": "LOW", "score": 73.0},
            {"ambulance_id": "AMB003", "eta_minutes": 8, "capability_rating": "HIGH", "traffic_density": "LOW", "score": 87.0}
        ])
        df_amb = pd.DataFrame(amb_opts)
        if "ambulance_id" in df_amb.columns:
            df_amb["AI_Status"] = df_amb["ambulance_id"].apply(lambda x: "🏆 SELECTED" if x == sel_amb.get("ambulance_id") else "Candidate")
        st.dataframe(df_amb, use_container_width=True)

    with col_tbl2:
        st.markdown("###### 🏥 Regional Hospital Evaluation")
        hosp_opts = alloc_data.get("hospital_options", [
            {"hospital_id": "H001", "hospital_name": "City Emergency Hospital", "travel_time_minutes": 8, "icu_available": False, "trauma_center": True, "score": 65.0},
            {"hospital_id": "H002", "hospital_name": "Metro Trauma Center", "travel_time_minutes": 9, "icu_available": True, "trauma_center": True, "score": 94.0},
            {"hospital_id": "H003", "hospital_name": "St. Jude Memorial", "travel_time_minutes": 12, "icu_available": True, "trauma_center": False, "score": 72.0}
        ])
        df_hosp = pd.DataFrame(hosp_opts)
        if "hospital_name" in df_hosp.columns:
            df_hosp["AI_Status"] = df_hosp["hospital_name"].apply(lambda x: "🏆 SELECTED" if x == sel_hosp.get("hospital_name") else "Candidate")
        st.dataframe(df_hosp, use_container_width=True)

    # 4. REAL-TIME AMBULANCE RESPONSE TRACKER
    st.markdown("<br>##### 🚨 REAL-TIME EMERGENCY RESPONSE TRACKER", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="background: #0F172A; border: 1px solid #334155; border-radius: 10px; padding: 1rem; color: white;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                <div style="background: #065F46; color: #34D399; padding: 8px 14px; border-radius: 8px; font-size: 0.85rem; font-weight: 700;">
                    1. DISPATCHED 🟢<br><span style="font-size: 0.75rem; color: #A7F3D0;">Ambulance {sel_amb.get('ambulance_id')} assigned</span>
                </div>
                <div style="font-size: 1.2rem; color: #34D399;">➔</div>
                <div style="background: #1E293B; border: 1px solid #38BDF8; color: #38BDF8; padding: 8px 14px; border-radius: 8px; font-size: 0.85rem; font-weight: 700;">
                    2. EN ROUTE TO ACCIDENT 🚨<br><span style="font-size: 0.75rem; color: #93C5FD;">ETA: {sel_amb.get('response_time_minutes')} mins</span>
                </div>
                <div style="font-size: 1.2rem; color: #94A3B8;">➔</div>
                <div style="background: #1E293B; color: #94A3B8; padding: 8px 14px; border-radius: 8px; font-size: 0.85rem; font-weight: 600;">
                    3. PATIENT PICKUP 🚑<br><span style="font-size: 0.75rem; color: #64748B;">On scene triage</span>
                </div>
                <div style="font-size: 1.2rem; color: #94A3B8;">➔</div>
                <div style="background: #1E293B; color: #94A3B8; padding: 8px 14px; border-radius: 8px; font-size: 0.85rem; font-weight: 600;">
                    4. EN ROUTE TO HOSPITAL 🏥<br><span style="font-size: 0.75rem; color: #64748B;">Hospital ETA: {sel_hosp.get('travel_time_minutes')} mins</span>
                </div>
                <div style="font-size: 1.2rem; color: #94A3B8;">➔</div>
                <div style="background: #1E293B; color: #94A3B8; padding: 8px 14px; border-radius: 8px; font-size: 0.85rem; font-weight: 600;">
                    5. ARRIVED AT EMERGENCY 🏁<br><span style="font-size: 0.75rem; color: #64748B;">Handover complete</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 5. DYNAMIC RE-ALLOCATION INTERACTIVE SANDBOX
    st.markdown("<br>##### 🧪 DYNAMIC AUTOMATIC RE-ALLOCATION SANDBOX", unsafe_allow_html=True)
    st.caption("Simulate ambulance delay or hospital capacity surge to observe real-time AI re-allocation.")

    rcol1, rcol2 = st.columns(2)
    with rcol1:
        sim_amb_delay = st.checkbox("Simulate AMB001 Delay (Traffic Surge)", value=False)
    with rcol2:
        sim_hosp_icu_busy = st.checkbox("Simulate Metro Trauma Center ICU Saturation", value=False)

    from tools.emergency_resource_tools import ResourceAllocatorEngine
    acc_test_payload = {
        "accident_id": "ACC102",
        "road_name": selected_road,
        "severity": "CRITICAL",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "traffic_density": "HIGH"
    }

    unavail_ambs = ["AMB001"] if sim_amb_delay else []
    unavail_hosps = ["H002"] if sim_hosp_icu_busy else []

    realloc_res = ResourceAllocatorEngine.allocate_resources(acc_test_payload, amb_unavailable=unavail_ambs, hosp_unavailable=unavail_hosps)

    if sim_amb_delay or sim_hosp_icu_busy:
        st.markdown(
            f"""
            <div style="background: #0F172A; border: 2px dashed #F59E0B; border-radius: 10px; padding: 1.2rem; margin-top: 10px; color: white;">
                <div style="font-weight: 700; color: #F59E0B; font-size: 1rem; margin-bottom: 8px;">🔄 AUTOMATIC RE-ALLOCATION TRIGGERED</div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 10px; font-size: 0.88rem;">
                    <div style="background: #1E293B; padding: 10px; border-radius: 6px;"><b>Reallocated Ambulance:</b> <b style="color: #38BDF8;">{realloc_res['selected_ambulance']['ambulance_id']}</b></div>
                    <div style="background: #1E293B; padding: 10px; border-radius: 6px;"><b>Reallocated Hospital:</b> <b style="color: #34D399;">{realloc_res['selected_hospital']['hospital_name']}</b></div>
                    <div style="background: #1E293B; padding: 10px; border-radius: 6px;"><b>New Total ETA:</b> <b style="color: #FBBF24;">{realloc_res['total_estimated_time']} min</b></div>
                    <div style="background: #1E293B; padding: 10px; border-radius: 6px;"><b>New Score:</b> <b style="color: #34D399;">{realloc_res['decision_score']}/100</b></div>
                </div>
                <div style="margin-top: 8px; font-size: 0.82rem; color: #CBD5E1;"><b>Reallocation Reason:</b> {realloc_res['reason']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("ℹ️ *Disclaimer: Recommended Emergency Resource Allocation - Final dispatch and hospital decisions remain with authorized emergency personnel.*")

with tab_flood:
    st.markdown("#### 🌊 Flood & Waterlogging Traffic Intelligence Agent")
    st.caption("Detects, predicts, and monitors road flooding and waterlogging risks before severe traffic congestion or accidents occur by combining rainfall, elevation, historical flood frequency, and traffic speed data.")

    fl_data = full_report.get("flood_traffic") or {}
    fl_score = fl_data.get("flood_risk_score", 15)
    fl_level = fl_data.get("risk_level", "LOW")
    fl_status = fl_data.get("road_status", "SAFE")
    fl_rain = fl_data.get("rainfall_mm_per_hour", 0.0)
    fl_eta = fl_data.get("estimated_time_to_waterlogging", "None")
    fl_act = fl_data.get("recommended_action", "Road is safe. Continue standard traffic operations.")
    fl_alt = fl_data.get("alternate_route", "Ring Road Bypass")
    fl_elev = fl_data.get("road_elevation_meters", 5.2)

    # 1. 🌊 FLOOD RISK OVERVIEW BANNER
    banner_color = "#10B981" if fl_score <= 20 else ("#3B82F6" if fl_score <= 40 else ("#F59E0B" if fl_score <= 60 else "#EF4444"))
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #0F172A 0%, #0369A1 100%); border: 2px solid {banner_color}; border-radius: 12px; padding: 1.4rem; margin-bottom: 1.4rem; color: white;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; margin-bottom: 10px;">
                <div>
                    <span style="background: {banner_color}; color: white; padding: 4px 12px; border-radius: 6px; font-weight: 800; font-size: 0.82rem;">🌊 FLOOD RISK STATUS: {fl_level} ({fl_status})</span>
                    <h3 style="margin: 8px 0 2px 0; color: #38BDF8; font-size: 1.25rem;">Target Road: {selected_road}</h3>
                </div>
                <div style="text-align: right; background: #0C4A6E; padding: 8px 16px; border-radius: 8px; border: 1px solid #38BDF8;">
                    <div style="font-size: 0.75rem; color: #BAE6FD; font-weight: 600;">FLOOD RISK SCORE</div>
                    <div style="font-size: 1.6rem; font-weight: 900; color: {banner_color};">{fl_score}<span style="font-size: 0.9rem; color: #94A3B8;">/100</span></div>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; font-size: 0.85rem; margin-top: 12px;">
                <div style="background: #1E293B; padding: 10px; border-radius: 8px;"><b>Rainfall Rate:</b> <b style="color: #38BDF8;">{fl_rain} mm/hr</b></div>
                <div style="background: #1E293B; padding: 10px; border-radius: 8px;"><b>Road Elevation:</b> <b style="color: #FBBF24;">{fl_elev} meters</b></div>
                <div style="background: #1E293B; padding: 10px; border-radius: 8px;"><b>Estimated Waterlogging ETA:</b> <b style="color: #F87171;">{fl_eta}</b></div>
                <div style="background: #1E293B; padding: 10px; border-radius: 8px;"><b>Recommended Detour:</b> <b style="color: #34D399;">{fl_alt}</b></div>
            </div>
            <div style="margin-top: 12px; font-size: 0.85rem; color: #CBD5E1; background: #0F172A; padding: 10px 14px; border-radius: 6px; border-left: 4px solid #38BDF8;">
                <b>🧠 AI Flood Strategy:</b> {fl_act}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 2. LIVE METRICS & ROAD MAP MARKERS
    fcol1, fcol2 = st.columns(2)
    with fcol1:
        st.markdown(
            f"""
            <div style="background: #0F172A; border: 1px solid #38BDF8; border-radius: 10px; padding: 1rem; color: white;">
                <div style="font-weight: 700; color: #38BDF8; font-size: 0.98rem; margin-bottom: 8px;">🌧️ METEOROLOGICAL & ROAD HYDROLOGY HUD</div>
                <div style="font-size: 0.88rem; line-height: 1.6;">
                    <div><b>Rainfall Intensity:</b> <span style="color: #38BDF8; font-weight: 800;">{fl_rain} mm/hr</span></div>
                    <div><b>Historical Flood Risk Zone:</b> {fl_data.get('historical_flood_risk', 'HIGH')}</div>
                    <div><b>Drainage Capacity Status:</b> {fl_data.get('drainage_condition', 'POOR')}</div>
                    <div><b>IoT Water Level Sensor:</b> <span style="color: #FBBF24; font-weight: 700;">{fl_data.get('water_level', 'UNAVAILABLE')}</span></div>
                    <div><b>Current Traffic Speed:</b> {fl_data.get('vehicle_speed_kmh', 25.0)} km/h</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with fcol2:
        st.markdown(
            f"""
            <div style="background: #0F172A; border: 1px solid #34D399; border-radius: 10px; padding: 1rem; color: white;">
                <div style="font-weight: 700; color: #34D399; font-size: 0.98rem; margin-bottom: 8px;">🗺️ GEOSPATIAL ROAD FLOOD CLASSIFICATION</div>
                <div style="font-size: 0.88rem; line-height: 1.6;">
                    <div><b>Main Road:</b> <span style="color: {'#EF4444' if fl_score > 60 else '#34D399'}; font-weight: 800;">{'HIGH RISK / FLOODED' if fl_score > 60 else 'SAFE / MONITOR'}</span></div>
                    <div><b>Broadway Ave:</b> <span style="color: #FBBF24; font-weight: 700;">MONITOR (Elevation 8.1m)</span></div>
                    <div><b>Express Highway:</b> <span style="color: #34D399; font-weight: 700;">SAFE (Elevated 14.5m)</span></div>
                    <div><b>Harbor View Park:</b> <span style="color: #EF4444; font-weight: 700;">CRITICAL (Elevation 3.8m)</span></div>
                    <div><b>Active Alternate Route:</b> <span style="color: #38BDF8; font-weight: 700;">{fl_alt}</span></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 3. EARLY WARNING PREDICTION TIMELINE
    st.markdown("<br>##### ⏳ AI EARLY WARNING WATERLOGGING PREDICTION TIMELINE", unsafe_allow_html=True)
    st.caption("Predicts surface water accumulation before road flooding occurs to execute preventive traffic signal diversions.")

    tline = fl_data.get("early_warning_timeline", [])
    if not tline:
        tline = [
            {"time": "NOW", "step": "Heavy Rainfall / Runoff Ingress", "status": f"Rainfall: {fl_rain} mm/hr"},
            {"time": "10 MIN", "step": "Traffic Speed Sinks & Surface Pooling", "status": "Predicted Speed: 18.0 km/h"},
            {"time": "20 MIN", "step": "Drainage Saturation & Waterlogging Surge", "status": f"Flood Risk: {fl_score}%"},
            {"time": "35 MIN", "step": "Severe Waterlogging / Inundation", "status": f"Action: {fl_alt}"}
        ]

    st.markdown(
        f"""
        <div style="background: #0F172A; border: 1px solid #334155; border-radius: 10px; padding: 1rem; color: white;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                <div style="background: #0369A1; color: #BAE6FD; padding: 8px 12px; border-radius: 8px; font-size: 0.85rem; font-weight: 700;">
                    {tline[0]['time']}<br><span style="font-size: 0.75rem; color: white;">{tline[0]['step']}</span>
                </div>
                <div style="font-size: 1.2rem; color: #38BDF8;">➔</div>
                <div style="background: #1E293B; border: 1px solid #38BDF8; color: #38BDF8; padding: 8px 12px; border-radius: 8px; font-size: 0.85rem; font-weight: 700;">
                    {tline[1]['time']}<br><span style="font-size: 0.75rem; color: #93C5FD;">{tline[1]['step']}</span>
                </div>
                <div style="font-size: 1.2rem; color: #F59E0B;">➔</div>
                <div style="background: #1E293B; border: 1px solid #F59E0B; color: #FBBF24; padding: 8px 12px; border-radius: 8px; font-size: 0.85rem; font-weight: 700;">
                    {tline[2]['time']}<br><span style="font-size: 0.75rem; color: #FDE68A;">{tline[2]['step']}</span>
                </div>
                <div style="font-size: 1.2rem; color: #EF4444;">➔</div>
                <div style="background: #7F1D1D; color: #FCA5A5; padding: 8px 12px; border-radius: 8px; font-size: 0.85rem; font-weight: 700;">
                    {tline[3]['time']}<br><span style="font-size: 0.75rem; color: white;">{tline[3]['step']}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 4. INTERACTIVE WEATHER & RAINFALL SIMULATOR SANDBOX
    st.markdown("<br>##### 🧪 REAL-TIME RAINFALL & FLOOD RISK SIMULATOR SANDBOX", unsafe_allow_html=True)
    st.caption("Adjust live weather parameters to observe instant AI risk scoring and preventive traffic signal adjustments.")

    scol1, scol2, scol3 = st.columns(3)
    with scol1:
        sb_rain = st.slider("Rainfall Intensity (mm/hr)", 0.0, 120.0, float(fl_rain))
    with scol2:
        sb_elev = st.slider("Road Elevation (meters)", 2.0, 20.0, float(fl_elev))
    with scol3:
        sb_water_sensor = st.checkbox("Simulate IoT Water Depth Sensor", value=False)
        sb_water_cm = st.slider("Sensor Water Depth (cm)", 0.0, 50.0, 25.0) if sb_water_sensor else None

    from tools.flood_data_tools import FloodRiskCalculator
    sb_fl_res = FloodRiskCalculator.calculate_risk(
        road_name=selected_road,
        rainfall_mm_per_hour=sb_rain,
        vehicle_speed=max(10.0, 45.0 - (sb_rain * 0.3)),
        sensor_water_level_cm=sb_water_cm,
        override_elevation=sb_elev
    )

    st.markdown(
        f"""
        <div style="background: #0F172A; border: 2px dashed #38BDF8; border-radius: 10px; padding: 1.2rem; margin-top: 10px; color: white;">
            <div style="font-weight: 700; color: #38BDF8; font-size: 1rem; margin-bottom: 8px;">🔮 LIVE SIMULATED FLOOD PREDICTION OUTCOME</div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 10px; font-size: 0.88rem;">
                <div style="background: #1E293B; padding: 10px; border-radius: 6px;"><b>Simulated Flood Risk:</b> <b style="color: {'#34D399' if sb_fl_res['flood_risk_score'] < 40 else ('#FBBF24' if sb_fl_res['flood_risk_score'] < 70 else '#F87171')};">{sb_fl_res['flood_risk_score']}/100</b></div>
                <div style="background: #1E293B; padding: 10px; border-radius: 6px;"><b>Risk Level:</b> <b style="color: #38BDF8;">{sb_fl_res['risk_level']}</b></div>
                <div style="background: #1E293B; padding: 10px; border-radius: 6px;"><b>Predicted Congestion:</b> <b style="color: #FBBF24;">{sb_fl_res['predicted_congestion_pct']}%</b></div>
                <div style="background: #1E293B; padding: 10px; border-radius: 6px;"><b>Estimated Waterlogging:</b> <b style="color: #F87171;">{sb_fl_res['estimated_time_to_waterlogging']}</b></div>
            </div>
            <div style="margin-top: 8px; font-size: 0.82rem; color: #CBD5E1;"><b>AI Recommended Strategy:</b> {sb_fl_res['recommended_action']}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("ℹ️ *Note: Flood predictions combine meteorological radar telemetry, road hydrology, and historical flood frequency.*")

with tab_driver:


    st.markdown("#### 🛡️ Driver Behavior & Safety Intelligence Dashboard")
    st.caption("Continuously analyzes driver telemetry, computes Driver Safety Scores (0-100), detects 8 hazard violation categories, and predicts unsafe driving probability.")

    d_score = d_safe.get("safety_score", 100)
    d_risk = d_safe.get("risk_level", "LOW")
    d_tot_v = d_safe.get("total_violations", 0)
    d_hazard = d_safe.get("primary_hazard", "None")
    d_rec = d_safe.get("recommendation", "Maintain safe driving behavior")
    d_pred = d_safe.get("risk_prediction", {})
    d_viols = d_safe.get("violations", {})

    if d_score >= 80:
        score_color = "#059669"
        score_border = "#34D399"
    elif d_score >= 60:
        score_color = "#D97706"
        score_border = "#FBBF24"
    else:
        score_color = "#DC2626"
        score_border = "#EF4444"

    # 1. Driver Safety Metrics Cards
    dcol1, dcol2, dcol3, dcol4 = st.columns(4)
    with dcol1:
        st.markdown(
            f"""
            <div class='metric-box' style='border-left: 5px solid {score_border}; background: #0F172A; color: white;'>
                <div class='metric-head'>Driver Safety Score</div>
                <div class='metric-body' style='color: {score_border}; font-size: 2.4rem;'>{d_score}</div>
                <div class='metric-sub'>scale 0 to 100</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with dcol2:
        st.markdown(
            f"""
            <div class='metric-box' style='border-left: 4px solid {score_border}; background: #0F172A; color: white;'>
                <div class='metric-head'>Risk Level Classification</div>
                <div class='metric-body' style='font-size: 1.3rem; color: {score_border};'>{d_risk}</div>
                <div class='metric-sub'>Safety Risk Tier</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with dcol3:
        st.markdown(
            f"""
            <div class='metric-box' style='background: #0F172A; color: white;'>
                <div class='metric-head'>Total Violations Flagged</div>
                <div class='metric-body' style='color: #F87171;'>{d_tot_v}</div>
                <div class='metric-sub'>infraction count</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with dcol4:
        st.markdown(
            f"""
            <div class='metric-box' style='background: #0F172A; color: white;'>
                <div class='metric-head'>Pre-Crash Risk Prediction</div>
                <div class='metric-body' style='color: #38BDF8;'>{d_pred.get('probability', 'LOW')}</div>
                <div class='metric-sub'>Future Hazard Risk</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. Hazard & Recommendation Banner
    st.markdown(
        f"""
        <div style="background: #0F172A; border: 2px solid {score_border}; border-radius: 10px; padding: 1.2rem; margin-bottom: 1.2rem; color: white;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <div style="font-weight: 800; font-size: 1rem; color: #38BDF8;">🚨 PRIMARY DRIVING HAZARD: {d_hazard.upper()}</div>
                <div style="font-size: 0.82rem; color: #94A3B8;">Target Vehicle ID: <b>{d_safe.get('vehicle_id', 'VH101')}</b></div>
            </div>
            <div style="font-size: 0.88rem; color: #E2E8F0; background: #1E293B; padding: 10px; border-radius: 6px; border-left: 4px solid #38BDF8;">
                <b>🛡️ Safety Recommendation:</b> {d_rec}
            </div>
            <div style="margin-top: 8px; font-size: 0.82rem; color: #CBD5E1;">
                <b>🔮 Risk Intelligence Prediction:</b> {d_pred.get('statement', 'Driver maintains LOW probability of future unsafe driving.')}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 3. 8 Violation Categories Breakdown Grid
    st.markdown("##### 🚗 8 Driver Infraction Categories Breakdown")
    v_col1, v_col2 = st.columns(2)

    v_items = [
        ("🛑 Sudden Hard Braking", d_viols.get("sudden_braking", 0)),
        ("⛔ Wrong-Way Driving", d_viols.get("wrong_way", 0)),
        ("🏎️ Speed Limit Breach", d_viols.get("overspeeding", 0)),
        ("🔄 Unauthorized U-Turn", d_viols.get("illegal_u_turn", 0)),
        ("🔀 Unsafe Lane Drift", d_viols.get("lane_violations", 0)),
        ("🚗 Tailgating Distance Violation", 0),
        ("📱 Distracted Driving (Phone Use)", 0),
        ("🔴 Red Light Running", 0)
    ]

    with v_col1:
        for label, count in v_items[:4]:
            v_color = "#F87171" if count > 0 else "#34D399"
            v_bg = "#7F1D1D" if count > 0 else "#064E3B"
            st.markdown(
                f"""
                <div style="background: #0F172A; border: 1px solid #334155; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; color: white;">
                    <span style="font-weight: 600; font-size: 0.88rem;">{label}</span>
                    <span style="background: {v_bg}; color: {v_color}; font-weight: 800; padding: 4px 10px; border-radius: 6px; font-size: 0.85rem;">{count} Detected</span>
                </div>
                """,
                unsafe_allow_html=True
            )

    with v_col2:
        for label, count in v_items[4:]:
            v_color = "#F87171" if count > 0 else "#34D399"
            v_bg = "#7F1D1D" if count > 0 else "#064E3B"
            st.markdown(
                f"""
                <div style="background: #0F172A; border: 1px solid #334155; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; color: white;">
                    <span style="font-weight: 600; font-size: 0.88rem;">{label}</span>
                    <span style="background: {v_bg}; color: {v_color}; font-weight: 800; padding: 4px 10px; border-radius: 6px; font-size: 0.85rem;">{count} Detected</span>
                </div>
                """,
                unsafe_allow_html=True
            )

    # 4. Interactive Test Case Selector
    st.markdown("<br>##### 🧪 Interactive Driver Behavior Telemetry Tester", unsafe_allow_html=True)
    st.caption("Select a pre-configured driver telemetry scenario to evaluate the Driver Behavior & Safety Agent in real-time.")

    from tools.driver_behavior_tools import DriverBehaviorTools
    tc_list = DriverBehaviorTools.get_test_cases()
    tc_names = [tc["case_name"] for tc in tc_list]
    sel_tc_name = st.selectbox("Select Driver Telemetry Scenario", tc_names)

    sel_tc = next(tc for tc in tc_list if tc["case_name"] == sel_tc_name)
    eval_res = DriverBehaviorTools.evaluate_telemetry(sel_tc["telemetry"])

    st.markdown(
        f"""
        <div style="background: #0F172A; border: 2px dashed #E11D48; border-radius: 10px; padding: 1.2rem; margin-top: 10px; color: white;">
            <div style="font-weight: 700; color: #E11D48; font-size: 1rem; margin-bottom: 8px;">🛡️ EVALUATION RESULT FOR {sel_tc_name.upper()}</div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 10px; font-size: 0.88rem;">
                <div style="background: #1E293B; padding: 10px; border-radius: 6px;"><b>Vehicle ID:</b> <b style="color: #38BDF8;">{eval_res['vehicle_id']}</b></div>
                <div style="background: #1E293B; padding: 10px; border-radius: 6px;"><b>Safety Score:</b> <b style="color: #34D399;">{eval_res['safety_score']}/100</b></div>
                <div style="background: #1E293B; padding: 10px; border-radius: 6px;"><b>Risk Level:</b> <b style="color: #F87171;">{eval_res['risk_level']}</b></div>
                <div style="background: #1E293B; padding: 10px; border-radius: 6px;"><b>Primary Hazard:</b> <b style="color: #FBBF24;">{eval_res['primary_hazard']}</b></div>
            </div>
            <div style="margin-top: 8px; font-size: 0.82rem; color: #94A3B8;"><b>Actionable Recommendation:</b> {eval_res['recommendation']}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with tab_gis:


    st.markdown("#### 🗺️ Geospatial GIS Visualizer & Google Maps Layer")
    st.caption("Multi-engine geospatial mapping with Google Maps Satellite Hybrid and PyDeck 3D pillars")

    gis_engine = st.radio("Select Mapping Engine", ["🗺️ Google Maps (Real Streets & Satellite + Direct Links)", "📊 PyDeck 3D Density Pillars"], horizontal=True)

    map_data = []
    recent_reports = get_latest_reports(limit=25)
    
    road_report_map = {}
    for r in recent_reports:
        r_name = r.get("road_name")
        if r_name not in road_report_map:
            road_report_map[r_name] = r.get("full_report", {})

    for r_name, coords in ROAD_COORDINATES.items():
        rep = road_report_map.get(r_name, {})
        t_info = rep.get("traffic_report", {})
        c_info = rep.get("congestion_prediction", {})
        e_info = rep.get("emergency_corridor", {})
        
        v_count = t_info.get("vehicles", 40)
        avg_spd = t_info.get("average_speed", 35.0)
        density = t_info.get("density", "Medium")
        has_emerg = e_info.get("green_corridor_active", False)
        has_acc = t_info.get("accident", False)

        if has_emerg:
            color_rgb = [239, 68, 68, 255]
            color_hex = "#DC2626"
            status_text = "🚨 EMERGENCY CORRIDOR ACTIVE"
        elif has_acc:
            color_rgb = [245, 158, 11, 255]
            color_hex = "#D97706"
            status_text = "⚠️ ACCIDENT DETECTED"
        elif density == "Low":
            color_rgb = [16, 185, 129, 200]
            color_hex = "#059669"
            status_text = "🟢 Low Density (Smooth Flow)"
        elif density == "Medium":
            color_rgb = [245, 158, 11, 200]
            color_hex = "#D97706"
            status_text = "🟡 Medium Density"
        else:
            color_rgb = [239, 68, 68, 220]
            color_hex = "#DC2626"
            status_text = "🔴 High / Critical Density"

        gmaps_url = f"https://www.google.com/maps/search/?api=1&query={coords['lat']},{coords['lon']}"

        map_data.append({
            "road": r_name,
            "lat": coords["lat"],
            "lon": coords["lon"],
            "vehicles": v_count,
            "speed": avg_spd,
            "elevation": v_count * 8,
            "density": density,
            "color": color_rgb,
            "color_hex": color_hex,
            "radius": 350 if has_emerg else 240,
            "status_text": status_text,
            "gmaps_url": gmaps_url
        })

    df_map = pd.DataFrame(map_data)

    if "Google Maps" in gis_engine and FOLIUM_AVAILABLE:
        st.markdown("##### 🛰️ Google Maps Hybrid Satellite Layer")
        
        m = folium.Map(location=[12.9720, 77.5950], zoom_start=13, tiles=None)

        folium.TileLayer(
            tiles="http://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
            attr="Google Maps Streets",
            name="Google Streets",
            overlay=False,
            control=True
        ).add_to(m)

        folium.TileLayer(
            tiles="http://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
            attr="Google Maps Hybrid Satellite",
            name="Google Satellite (Hybrid)",
            overlay=False,
            control=True
        ).add_to(m)

        folium.LayerControl().add_to(m)

        for row in map_data:
            popup_html = f"""
            <div style="font-family: Inter, sans-serif; width: 210px; color: #1E293B;">
                <h4 style="margin: 0 0 6px 0; color: #0284C7;">📍 {row['road']}</h4>
                <p style="margin: 3px 0;"><b>Status:</b> {row['status_text']}</p>
                <p style="margin: 3px 0;"><b>Vehicles:</b> {row['vehicles']} cars</p>
                <p style="margin: 3px 0;"><b>Average Speed:</b> {row['speed']} km/h</p>
                <hr style="margin: 8px 0; border: 0; border-top: 1px solid #E2E8F0;">
                <a href="{row['gmaps_url']}" target="_blank" 
                   style="background: #2563EB; color: white; padding: 6px 12px; border-radius: 4px; text-decoration: none; display: inline-block; font-weight: 600; font-size: 11px;">
                   🗺️ Open in Google Maps
                </a>
            </div>
            """
            
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=14,
                popup=folium.Popup(popup_html, max_width=260),
                color=row["color_hex"],
                fill=True,
                fill_color=row["color_hex"],
                fill_opacity=0.8,
                tooltip=f"{row['road']}: {row['vehicles']} vehicles"
            ).add_to(m)

        st_folium(m, width="100%", height=480)

        st.markdown("##### 🔗 Direct Google Maps Junction Links")
        link_cols = st.columns(len(map_data))
        for idx, row in enumerate(map_data):
            with link_cols[idx]:
                st.markdown(f"[{row['road']}]({row['gmaps_url']})")

    else:
        st.markdown("##### 📊 PyDeck 3D Elevation Pillars Map")
        view_state = pdk.ViewState(latitude=12.9720, longitude=77.5950, zoom=12.5, pitch=45.0, bearing=15.0)

        column_layer = pdk.Layer(
            "ColumnLayer",
            data=df_map,
            get_position=["lon", "lat"],
            get_elevation="elevation",
            elevation_scale=1.5,
            radius=150,
            get_fill_color="color",
            pickable=True,
            auto_highlight=True
        )

        scatter_layer = pdk.Layer(
            "ScatterplotLayer",
            data=df_map,
            get_position=["lon", "lat"],
            get_color="color",
            get_radius="radius",
            pickable=True
        )

        deck = pdk.Deck(
            layers=[column_layer, scatter_layer],
            initial_view_state=view_state,
            map_style="mapbox://styles/mapbox/light-v10",
            tooltip={"text": "{road}\nDensity: {density}\nVehicles: {vehicles}\nStatus: {status_text}"}
        )

        st.pydeck_chart(deck, use_container_width=True)

with tab2:
    st.markdown("#### 🚨 Emergency Response Status & Dynamic Signal Control")

    # 1. Emergency Status Summary Card
    has_emerg = (e_corr.get("emergency_detected", False) or t_rep.get("accident_status", False) or e_corr.get("green_corridor_active", False))
    status_badge_bg = "#DC2626" if has_emerg else "#059669"
    status_text = f"🚨 EMERGENCY MODE ACTIVE ({e_corr.get('event_type', 'ACCIDENT')})" if has_emerg else "🟢 NORMAL ADAPTIVE OPERATIONS"

    st.markdown(
        f"""
        <div style="background: #0F172A; border: 2px solid {status_badge_bg}; border-radius: 12px; padding: 1.2rem; margin-bottom: 1.2rem; color: white;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; margin-bottom: 10px;">
                <div style="font-size: 1.1rem; font-weight: 700; color: {status_badge_bg};">{status_text}</div>
                <div style="font-size: 0.85rem; color: #94A3B8;">📍 Location: <b>{selected_road}</b> ({current_telemetry.get('latitude', 13.0827)}, {current_telemetry.get('longitude', 80.2707)})</div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; font-size: 0.88rem;">
                <div style="background: #1E293B; padding: 10px; border-radius: 8px;"><b>⚠️ Accident Detected:</b> <span style="color: {'#EF4444' if t_rep.get('accident_status') else '#34D399'};">{"YES" if t_rep.get('accident_status') else "NO"}</span></div>
                <div style="background: #1E293B; padding: 10px; border-radius: 8px;"><b>🔥 Severity:</b> <span style="color: {'#EF4444' if e_corr.get('severity') == 'CRITICAL' else '#F59E0B'};">{e_corr.get('severity', 'NORMAL')}</span></div>
                <div style="background: #1E293B; padding: 10px; border-radius: 8px;"><b>🚑 Emergency Vehicle:</b> <span style="color: #38BDF8;">{e_corr.get('vehicle_type', 'NONE')}</span></div>
                <div style="background: #1E293B; padding: 10px; border-radius: 8px;"><b>🚦 Green Corridor:</b> <span style="color: {'#34D399' if e_corr.get('green_corridor_active') else '#94A3B8'};">{"ACTIVE" if e_corr.get('green_corridor_active') else "INACTIVE"}</span></div>
                <div style="background: #1E293B; padding: 10px; border-radius: 8px;"><b>⏱️ Signal Extension:</b> <span style="color: #38BDF8;">+{s_opt.get('dynamic_increase_sec', 0)}s</span></div>
                <div style="background: #1E293B; padding: 10px; border-radius: 8px;"><b>📢 Citizen Alert:</b> <span style="color: #34D399;">SENT</span></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 2. Side-by-side Signal Timer Visualization Component
    col_sig1, col_sig2 = st.columns([1, 1])

    with col_sig1:
        st.markdown("##### 🟢 NORMAL SIGNAL TIMING")
        st.markdown(
            """
            <div style="background: #1E293B; border-radius: 8px; padding: 12px; margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; font-weight: 600; color: #34D399; font-size: 0.9rem;">
                    <span>🟢 Green Phase</span><span>30 sec</span>
                </div>
                <div style="background: #334155; height: 10px; border-radius: 5px; margin: 4px 0 10px 0;">
                    <div style="background: #34D399; width: 46%; height: 10px; border-radius: 5px;"></div>
                </div>
                <div style="display: flex; justify-content: space-between; font-weight: 600; color: #FBBF24; font-size: 0.9rem;">
                    <span>🟡 Yellow Phase</span><span>5 sec</span>
                </div>
                <div style="background: #334155; height: 10px; border-radius: 5px; margin: 4px 0 10px 0;">
                    <div style="background: #FBBF24; width: 8%; height: 10px; border-radius: 5px;"></div>
                </div>
                <div style="display: flex; justify-content: space-between; font-weight: 600; color: #F87171; font-size: 0.9rem;">
                    <span>🔴 Red Phase</span><span>30 sec</span>
                </div>
                <div style="background: #334155; height: 10px; border-radius: 5px; margin: 4px 0;">
                    <div style="background: #F87171; width: 46%; height: 10px; border-radius: 5px;"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_sig2:
        mode_title = "🚨 EMERGENCY / GREEN CORRIDOR TIMING" if has_emerg else "⚡ ADAPTIVE DYNAMIC TIMING"
        curr_green = s_opt.get("recommended_green_time_sec", 50)
        curr_yellow = s_opt.get("recommended_yellow_time_sec", 5)
        curr_red = s_opt.get("recommended_red_time_sec", 15)

        st.markdown(f"##### {mode_title}")
        st.markdown(
            f"""
            <div style="background: #1E293B; border-radius: 8px; padding: 12px; margin-bottom: 10px; border: 1px solid {'#EF4444' if has_emerg else '#0284C7'};">
                <div style="display: flex; justify-content: space-between; font-weight: 600; color: #34D399; font-size: 0.9rem;">
                    <span>🟢 Green Phase (+{s_opt.get('dynamic_increase_sec', 0)}s)</span><span>{curr_green} sec</span>
                </div>
                <div style="background: #334155; height: 10px; border-radius: 5px; margin: 4px 0 10px 0;">
                    <div style="background: #34D399; width: {min(100, int((curr_green/110)*100))}%; height: 10px; border-radius: 5px;"></div>
                </div>
                <div style="display: flex; justify-content: space-between; font-weight: 600; color: #FBBF24; font-size: 0.9rem;">
                    <span>🟡 Yellow Phase</span><span>{curr_yellow} sec</span>
                </div>
                <div style="background: #334155; height: 10px; border-radius: 5px; margin: 4px 0 10px 0;">
                    <div style="background: #FBBF24; width: 8%; height: 10px; border-radius: 5px;"></div>
                </div>
                <div style="display: flex; justify-content: space-between; font-weight: 600; color: #F87171; font-size: 0.9rem;">
                    <span>🔴 Red Phase (Reduced Wait)</span><span>{curr_red} sec</span>
                </div>
                <div style="background: #334155; height: 10px; border-radius: 5px; margin: 4px 0;">
                    <div style="background: #F87171; width: {min(100, int((curr_red/110)*100))}%; height: 10px; border-radius: 5px;"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 3. AI Signal Decision Explanation Card
    ai_exp = s_opt.get("ai_explanation", {})
    st.markdown("##### 🧠 AI Signal Decision Explanation")
    st.markdown(
        f"""
        <div style="background: #0F172A; border: 1px solid #334155; border-radius: 8px; padding: 12px 16px; font-size: 0.88rem; color: #E2E8F0; margin-bottom: 1.2rem;">
            <div style="margin-bottom: 6px;"><b>Emergency Detected:</b> <span style="color: {'#EF4444' if ai_exp.get('emergency_detected') else '#34D399'};">{"YES" if ai_exp.get('emergency_detected') else "NO"}</span> | <b>Traffic Density:</b> {ai_exp.get('traffic_density', 'MEDIUM')} | <b>Priority Rescue Lane:</b> <span style="color: #00F2FE;">{e_corr.get('affected_lane', 'Lane 1')}</span></div>
            <div style="margin-bottom: 6px;"><b>Action Taken:</b> <span style="color: #38BDF8; font-weight: 700;">{ai_exp.get('action', 'Maintain standard timing')}</span> | <b>Throughput Speedup:</b> <span style="color: #34D399; font-weight: 700;">{s_opt.get('throughput_speedup', '+300%')}</span></div>
            <div style="margin-bottom: 6px; color: #94A3B8;"><b>Reason:</b> {ai_exp.get('reason', 'Normal operations')}</div>
            <div style="color: #34D399; font-size: 0.82rem;">✔️ {ai_exp.get('safety_notes', 'Safety interlocks verified')}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 4. Lane-by-Lane Fast Clearance Breakdown
    st.markdown("##### 🏎️ Lane-by-Lane Vehicle Clearance & Signal Light Duration")
    lane_bd = s_opt.get("lane_breakdown", {
        "Lane 1 (Emergency / Fast Rescue Lane)": {"green_sec": 90, "status": "🟢 FAST CLEARANCE LOCK"},
        "Lane 2 (Inner Traffic Lane)": {"green_sec": 45, "status": "🟡 ADAPTIVE FLUSH"},
        "Lane 3 (Outer Divert Lane)": {"green_sec": 30, "status": "🔵 BYPASS DIVERSION"}
    })

    lane_cols = st.columns(len(lane_bd))
    for idx, (l_name, l_info) in enumerate(lane_bd.items()):
        with lane_cols[idx]:
            is_prio = ("FAST" in l_info.get("status", "") or "EMERGENCY" in l_name.upper())
            card_border = "#EF4444" if (is_prio and has_emerg) else "#0284C7"
            st.markdown(
                f"""
                <div style="background: #0F172A; border: 2px solid {card_border}; border-radius: 8px; padding: 12px; text-align: center; color: white; margin-bottom: 1.2rem;">
                    <div style="font-weight: 700; font-size: 0.85rem; color: #38BDF8; margin-bottom: 6px;">{l_name}</div>
                    <div style="font-size: 1.4rem; font-weight: 800; color: {'#34D399' if is_prio else '#FBBF24'};">{l_info.get('green_sec', 30)}s Green</div>
                    <div style="font-size: 0.78rem; font-weight: 600; margin-top: 4px; color: #E2E8F0;">{l_info.get('status', '🟢 NORMAL')}</div>
                </div>
                """,
                unsafe_allow_html=True
            )


    st.subheader("Intersections Grid Status Table")
    junction_data = []
    for r_name in ROADS:
        is_active_road = (r_name == selected_road)
        g_sec = s_opt.get('recommended_green_time_sec') if is_active_road else 30
        mode = s_opt.get('signal_mode') if is_active_road else "Standard"
        junction_data.append({
            "Junction / Road": r_name,
            "Signal Mode": mode,
            "Green Phase (sec)": g_sec,
            "Status": "🟢 Green Lock" if (is_active_road and e_corr.get("green_corridor_active")) else "🟡 Adaptive"
        })
    st.dataframe(pd.DataFrame(junction_data), use_container_width=True)


with tab3:
    st.markdown("#### 📢 Citizen Broadcast Feed & WhatsApp Alert Simulator")
    st.caption("Multi-channel citizen alerting platform with real-time WhatsApp, SMS, and VMS Highway sign broadcasts")

    alerts_list = get_active_alerts(limit=15)
    col_phone, col_table = st.columns([1, 2])

    with col_phone:
        st.markdown("##### 📱 Live Citizen WhatsApp Feed Mockup")
        
        latest_alert = alerts_list[0] if alerts_list else {
            "title": f"🚨 EMERGENCY CORRIDOR - {selected_road.upper()}",
            "message": f"Priority Green Corridor operational on {selected_road}. All non-emergency vehicles divert immediately.",
            "severity": "EMERGENCY",
            "alternate_route": c_pred.get("recommended_alternate_roads", ["Outer Bypass"])[0],
            "timestamp": datetime.utcnow().strftime("%H:%M")
        }

        sev_bg = "#25D366" if latest_alert.get("severity") == "INFO" else ("#34B7F1" if latest_alert.get("severity") == "WARNING" else "#DC2626")

        whatsapp_html = f"""
        <div style="width: 100%; max-width: 360px; border-radius: 20px; overflow: hidden; border: 4px solid #334155; box-shadow: 0 10px 25px rgba(0,0,0,0.5); font-family: Inter, sans-serif; margin: 0 auto; background: #0F172A;">
            <!-- Phone Notch Header -->
            <div style="background: #075E54; color: white; padding: 12px 16px; display: flex; align-items: center; gap: 10px;">
                <div style="width: 36px; height: 36px; border-radius: 50%; background: #128C7E; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: bold;">
                    🚦
                </div>
                <div>
                    <div style="font-weight: 700; font-size: 14px; color: #FFFFFF !important;">SmartCity Dispatch Bot ✔️</div>
                    <div style="font-size: 11px; color: #E0F2F1 !important;">Verified Official Channel • Online</div>
                </div>
            </div>
            
            <!-- Chat Wall -->
            <div style="background: #0B0F19; padding: 14px; min-height: 280px; display: flex; flex-direction: column; gap: 10px;">
                <div style="align-self: center; background: #1E293B; color: #38BDF8 !important; padding: 4px 10px; border-radius: 6px; font-size: 10px; font-weight: 600; border: 1px solid #334155;">
                    🔒 End-to-end encrypted official advisory feed
                </div>
                
                <!-- Incoming Broadcast Bubble -->
                <div style="background: #1E293B; border-radius: 8px 8px 8px 0px; padding: 10px 12px; max-width: 90%; box-shadow: 0 2px 6px rgba(0,0,0,0.3); border-left: 4px solid {sev_bg}; border: 1px solid #334155;">
                    <div style="font-weight: 800; font-size: 12px; color: {sev_bg} !important; margin-bottom: 4px;">
                        {latest_alert.get('title', 'TRAFFIC ADVISORY')}
                    </div>
                    <div style="font-size: 12px; color: #F8FAFC !important; line-height: 1.4;">
                        {latest_alert.get('message', 'Drive safely.')}
                    </div>
                    {f"<div style='margin-top: 6px; padding: 4px 8px; background: #0F172A; border-radius: 4px; font-size: 11px; color: #60A5FA !important; font-weight: 600;'>🛣️ Reroute: {latest_alert.get('alternate_route')}</div>" if latest_alert.get('alternate_route') else ""}
                    <div style="text-align: right; font-size: 9px; color: #94A3B8 !important; margin-top: 4px;">
                        {latest_alert.get('timestamp', 'Just now')[:16]} <span style="color: #34B7F1;">✓✓</span>
                    </div>
                </div>
            </div>
        </div>
        """
        st.components.v1.html(whatsapp_html, height=360)


        st.markdown("---")
        st.markdown("##### 📡 Cellular SMS Dispatcher (No WhatsApp Account Needed)")
        user_phone = st.text_input("Enter Recipient Mobile Phone Number", value="+916383258373", help="Works on any cellular phone. No WhatsApp account or app required.")
        
        with st.expander("🔑 Live SMS Gateway API Settings (For Real Physical Phone SMS Delivery)"):
            st.caption("To receive real SMS on your physical mobile phone via Indian telecom networks (Airtel, Jio, Vi) or Global carriers:")
            fast2sms_key = st.text_input("Fast2SMS Free API Key (For India Numbers)", type="password", help="Get free instant API key at www.fast2sms.com")
            twilio_sid = st.text_input("Twilio Account SID (Optional)", type="password")
            twilio_auth = st.text_input("Twilio Auth Token (Optional)", type="password")
            twilio_num = st.text_input("Twilio SMS Sender Number (Optional)", value="+18005550199")

        # Prepare SMS alert payload
        alert_title_txt = latest_alert.get('title', 'TRAFFIC ADVISORY')
        alert_body_txt = latest_alert.get('message', 'Traffic updates.')
        reroute_txt = f" Reroute: {latest_alert.get('alternate_route')}" if latest_alert.get('alternate_route') else ""

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("📡 Dispatch Direct Cellular SMS (No WhatsApp Needed)", use_container_width=True):
                with st.spinner(f"Dispatching direct Cellular SMS to {user_phone}..."):
                    sms_res = send_cellular_sms(
                        phone_number=user_phone,
                        alert_data=latest_alert,
                        fast2sms_api_key=fast2sms_key,
                        twilio_sid=twilio_sid,
                        twilio_auth=twilio_auth,
                        twilio_number=twilio_num
                    )
                    if sms_res.get("status") == "DELIVERED_TO_PHYSICAL_PHONE":
                        st.success(f"🎉 REAL SMS DELIVERED TO PHYSICAL PHONE {user_phone}!")
                    elif sms_res.get("status") == "SIMULATION_MODE":
                        st.info(f"ℹ️ {sms_res.get('notice')}")
                    else:
                        st.warning(f"⚠️ {sms_res.get('status')}: {sms_res.get('error', 'Check API key')}")
                    st.json(sms_res)

        with col_b2:
            import urllib.parse
            full_wa_text = f"{alert_title_txt}\n\n{alert_body_txt}{reroute_txt}\n\n- SmartCity Traffic AI Dispatch"
            encoded_wa_text = urllib.parse.quote(full_wa_text)
            clean_phone = "".join(filter(str.isdigit, user_phone))
            wa_url = f"https://wa.me/{clean_phone}?text={encoded_wa_text}"
            
            st.markdown(
                f"""
                <a href="{wa_url}" target="_blank" style="text-decoration: none;">
                    <div style="background-color: #25D366; color: white !important; font-weight: 700; text-align: center; padding: 7px 12px; border-radius: 6px; font-size: 13px;">
                        💬 Optional: WhatsApp Web Chat
                    </div>
                </a>
                """,
                unsafe_allow_html=True
            )

    with col_table:
        st.markdown("##### 📋 Citizen Broadcast History Table")
        alerts_list = get_active_alerts(limit=15)
        if alerts_list:
            df_alerts = pd.DataFrame(alerts_list)[["timestamp", "severity", "title", "road_name", "message", "alternate_route"]]
            st.dataframe(df_alerts, use_container_width=True)
        else:
            st.info("No active public alerts currently broadcasted.")

with tab4:
    st.markdown("#### 📈 Analytics & Carbon Footprint Sustainability")
    
    col_pdf1, col_pdf2 = st.columns([3, 1])
    with col_pdf1:
        st.caption("City-wide vehicle throughput, peak traffic trends, and carbon reduction metrics.")
    with col_pdf2:
        pdf_data = generate_traffic_pdf_report(
            road_name=selected_road,
            reports=get_latest_reports(limit=30),
            analytics=get_analytics_summary(limit=30),
            alerts=get_active_alerts(limit=30)
        )

        st.download_button(
            label="📥 Export Executive PDF Report",
            data=pdf_data,
            file_name=f"Traffic_Analytics_{selected_road.replace(' ', '_')}_{datetime.utcnow().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    analytics_data = get_analytics_summary(limit=30)

    if analytics_data:
        df_analytics = pd.DataFrame(analytics_data)

        c_graph1, c_graph2 = st.columns(2)
        with c_graph1:
            fig_cong = px.line(
                df_analytics,
                x="timestamp",
                y="congestion_index",
                color="road_name",
                title="Congestion Index Trend Over Time",
                markers=True,
                template="plotly_dark"
            )
            fig_cong.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_cong, use_container_width=True)

        with c_graph2:
            fig_co2 = px.bar(
                df_analytics,
                x="road_name",
                y="carbon_emission_kg",
                color="congestion_index",
                title="Carbon Emission (CO2 kg) by Road",
                color_continuous_scale="Reds",
                template="plotly_dark"
            )
            fig_co2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_co2, use_container_width=True)
    else:
        st.info("Run simulation ticks to populate analytics graphs.")

with tab5:
    st.markdown("#### 🛡️ V2I Pre-Crash Safety Intelligence Dashboard")
    st.caption("Real-time collision probability scoring and Vehicle-to-Infrastructure (V2I) ECU command broadcasts")

    v2i_col1, v2i_col2, v2i_col3, v2i_col4 = st.columns(4)

    risk_score = v2i.get('accident_risk_score', 0)
    alert_level = v2i.get('alert_level', 'LOW')

    if risk_score >= 80:
        risk_color = "#DC2626"
        risk_bg = "#FEF2F2"
    elif risk_score >= 65:
        risk_color = "#D97706"
        risk_bg = "#FFFBEB"
    elif risk_score >= 40:
        risk_color = "#CA8A04"
        risk_bg = "#FEFCE8"
    else:
        risk_color = "#059669"
        risk_bg = "#ECFDF5"

    with v2i_col1:
        st.markdown(
            f"""
            <div class='metric-box' style='border-left: 5px solid {risk_color}; background: {risk_bg};'>
                <div class='metric-head'>Accident Risk Score</div>
                <div class='metric-body' style='color: {risk_color}; font-size: 2.5rem;'>{risk_score}</div>
                <div class='metric-sub'>scale 0 to 100</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with v2i_col2:
        level_emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MODERATE": "🟡", "LOW": "🟢"}.get(alert_level, "⚪")
        st.markdown(
            f"""
            <div class='metric-box' style='border-left: 4px solid {risk_color};'>
                <div class='metric-head'>Alert Level</div>
                <div class='metric-body' style='font-size: 1.3rem; color: {risk_color};'>{level_emoji} {alert_level}</div>
                <div class='metric-sub'>V2I threat classification</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with v2i_col3:
        st.markdown(
            f"""
            <div class='metric-box'>
                <div class='metric-head'>Connected Vehicles</div>
                <div class='metric-body'>{v2i.get('connected_vehicles_in_zone', 0)}</div>
                <div class='metric-sub'>{v2i.get('vehicles_receiving_signal', 0)} receiving V2I signal</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with v2i_col4:
        st.markdown(
            f"""
            <div class='metric-box'>
                <div class='metric-head'>Signal Latency</div>
                <div class='metric-body'>{v2i.get('signal_latency_ms', 0)} ms</div>
                <div class='metric-sub'>{v2i.get('v2i_protocol', 'DSRC')}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")

    # Action Taken Banner
    action_text = v2i.get('action_taken', 'No action required.')
    if alert_level == "CRITICAL":
        banner_class = "banner-critical"
    elif alert_level == "HIGH":
        banner_class = "banner-warning"
    else:
        banner_class = "banner-info"
    st.markdown(f"<div class='{banner_class}'>{action_text}</div>", unsafe_allow_html=True)

    st.markdown("---")

    # ECU Commands and Risk Breakdown side by side
    ecu_col, risk_col = st.columns(2)

    with ecu_col:
        st.markdown("##### 🚗 V2I ECU Commands Broadcast to Connected Vehicles")
        ecu = v2i.get('v2i_ecu_commands', {})
        ecu_items = [
            ("🎯 Airbag Armed", ecu.get('arm_airbag', False)),
            ("🪢 Seatbelt Pre-Tensioned", ecu.get('pre_tension_seatbelt', False)),
            ("🛑 AEB (Auto Emergency Brake)", ecu.get('aeb_brake', False)),
            ("⚡ Hazard Lights Flash", ecu.get('hazard_lights_flash', False)),
            ("🪟 Windows Auto-Closed", ecu.get('close_windows', False)),
            ("🪑 Headrest Adjusted", ecu.get('adjust_headrest', False)),
        ]
        for label, active in ecu_items:
            status = "✅ ACTIVATED" if active else "⬜ Standby"
            color = "#059669" if active else "#94A3B8"
            st.markdown(f"<span style='color: {color}; font-weight: 600; font-size: 0.92rem;'>{label}: {status}</span>", unsafe_allow_html=True)

        if ecu.get('reduce_speed_limit_kmh'):
            st.markdown(f"<span style='color: #DC2626; font-weight: 700; font-size: 0.92rem;'>🚨 Speed Limit Override: {ecu['reduce_speed_limit_kmh']} km/h</span>", unsafe_allow_html=True)
        if ecu.get('estimated_impact_seconds'):
            st.markdown(f"<span style='color: #DC2626; font-weight: 700; font-size: 0.92rem;'>⏱️ Est. Impact: {ecu['estimated_impact_seconds']}s</span>", unsafe_allow_html=True)

    with risk_col:
        st.markdown("##### 📊 Risk Score Breakdown (Weighted Factors)")
        breakdown = v2i.get('risk_breakdown', {})
        breakdown_items = [
            ("🌧️ Weather Hazard", breakdown.get('weather_risk', 0), 25),
            ("🚗 Speed Danger Zone", breakdown.get('speed_risk', 0), 20),
            ("👥 Vehicle Overcrowding", breakdown.get('overcrowding_risk', 0), 20),
            ("📈 Congestion Volatility", breakdown.get('congestion_risk', 0), 15),
            ("🕐 Time-of-Day Risk", breakdown.get('time_of_day_risk', 0), 10),
            ("🚨 Active Incident", breakdown.get('active_incident_risk', 0), 10),
        ]
        for label, value, max_val in breakdown_items:
            pct = min(100, (value / max_val) * 100) if max_val > 0 else 0
            bar_color = "#DC2626" if pct > 70 else ("#D97706" if pct > 40 else "#059669")
            st.markdown(
                f"""
                <div style='margin-bottom: 8px;'>
                    <div style='display: flex; justify-content: space-between; font-size: 0.82rem; color: #334155; font-weight: 600;'>
                        <span>{label}</span>
                        <span>{value} / {max_val}</span>
                    </div>
                    <div style='background: #E2E8F0; border-radius: 4px; height: 8px; margin-top: 3px;'>
                        <div style='background: {bar_color}; width: {pct}%; height: 8px; border-radius: 4px;'></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )





