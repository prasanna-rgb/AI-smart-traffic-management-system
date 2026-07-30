"""
Streamlit Web Dashboard for AI Smart Traffic Management System.
Features live telemetry, agent decision tracking, emergency alerts, signal controls, and analytics charts.
"""
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
from datetime import datetime

from config.settings import APP_NAME, VERSION
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
from tools.vision_simulator import VisionSimulator
from tools.whatsapp_notifier import WhatsAppNotifier
from tools.driver_behavior import DriverBehaviorAnalyzer
from tools.driver_behavior_tools import DriverBehaviorTools
from crew import run_traffic_crew
import pydeck as pdk


try:
    import folium
    from streamlit_folium import st_folium
    FOLIUM_AVAILABLE = True
except Exception:
    FOLIUM_AVAILABLE = False

# Ensure DB initialized
init_db()

# Page Setup
st.set_page_config(
    page_title="AI Smart Traffic Management System",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Coordinates dictionary for city junctions
ROAD_COORDINATES = {
    "Main Road": {"lat": 12.9716, "lon": 77.5946},
    "Broadway Ave": {"lat": 12.9800, "lon": 77.6000},
    "Express Highway": {"lat": 12.9600, "lon": 77.6100},
    "Downtown Ring": {"lat": 12.9650, "lon": 77.5850},
    "Harbor View Park": {"lat": 12.9850, "lon": 77.5750}
}

# Custom CSS styling for premium look with high contrast fonts
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: #0B0F19 !important;
        color: #F8FAFC !important;
    }

    /* Streamlit Top Navbar Header Dark Mode */
    header[data-testid="stHeader"], [data-testid="stHeader"], .stHeader, [data-testid="stToolbar"], [data-testid="stDecoration"], nav, header {
        background-color: #0B0F19 !important;
        background: #0B0F19 !important;
        color: #F8FAFC !important;
    }
    header[data-testid="stHeader"] *, [data-testid="stHeader"] * {
        color: #F8FAFC !important;
    }


    /* Universal Text Contrast */
    h1, h2, h3, h4, h5, h6, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }

    p, span, label, legend, [data-testid="stWidgetLabel"] {
        color: #E2E8F0 !important;
    }


    /* Sidebar Container Styling (Dark High Contrast) */
    [data-testid="stSidebar"], [data-testid="stSidebarNav"], section[data-testid="stSidebar"] {
        background-color: #111827 !important;
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


    /* BaseWeb Dropdown Popover Menus & Selectboxes (Dark Mode Fix) */
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"], li[role="option"], [data-baseweb="popover"] * {
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
    div[data-testid="stAlert"] p, div[data-testid="stAlert"] div {
        color: #F8FAFC !important;
    }

    /* Dataframes & Tables Contrast */
    [data-testid="stDataFrame"], div[data-testid="stTable"] {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }
    [data-testid="stDataFrame"] *, div[data-testid="stTable"] table, div[data-testid="stTable"] * {
        color: #F8FAFC !important;
    }

    /* Form Text Inputs & Text Areas (Dark Mode Contrast Fix) */
    div[data-baseweb="input"] input, textarea, div[data-baseweb="textarea"] textarea {
        background-color: #1E293B !important;
        color: #F8FAFC !important;
        border-color: #334155 !important;
        font-size: 0.95rem !important;
    }
    
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div {
        background-color: #1E293B !important;
        border-color: #334155 !important;
    }

    /* Input Labels, Captions, & Tooltips */
    .stTextInput label, .stTextArea label, .stSelectbox label {
        color: #F8FAFC !important;
        font-weight: 600 !important;
    }
    
    .stTextInput small, .stTextArea small, [data-testid="stMarkdownContainer"] caption, .stCaption {
        color: #CBD5E1 !important;
    }

    /* Code Blocks & Pre Blocks (WhatsApp Preview Box) */
    div[data-testid="stCodeBlock"], pre, code, .stCodeBlock code {
        background-color: #0F172A !important;
        color: #38BDF8 !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        font-family: 'Consolas', 'Courier New', monospace !important;
    }
    
    div[data-testid="stCodeBlock"] * {
        color: #38BDF8 !important;
    }

    /* Buttons */
    button[kind="secondary"], button[kind="primary"], button[data-testid="baseButton-secondary"] {
        background-color: #1E293B !important;
        color: #38BDF8 !important;
        border: 1px solid #38BDF8 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    button[kind="secondary"]:hover, button[kind="primary"]:hover, button[data-testid="baseButton-secondary"]:hover {
        background-color: #38BDF8 !important;
        color: #0F172A !important;
    }

    .main-header {
        font-size: 2.4rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #38BDF8 0%, #34D399 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem !important;
    }
    .sub-header {
        color: #94A3B8 !important;
        font-size: 1.05rem !important;
        font-weight: 500 !important;
        margin-bottom: 1.5rem !important;
    }
    .metric-card {
        background: linear-gradient(145deg, #1E293B 0%, #0F172A 100%) !important;
        border-radius: 12px !important;
        padding: 1.2rem !important;
        border: 1px solid #334155 !important;
        border-left: 5px solid #3B82F6 !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3) !important;
    }
    .metric-title {
        color: #CBD5E1 !important;
        font-size: 0.85rem !important;
        text-transform: uppercase !important;
        font-weight: 700 !important;
        letter-spacing: 0.05em !important;
    }
    .metric-value {
        color: #FFFFFF !important;
        font-size: 1.9rem !important;
        font-weight: 800 !important;
        margin-top: 0.3rem !important;
    }
    .alert-banner-emergency {
        background: linear-gradient(90deg, #EF4444 0%, #B91C1C 100%) !important;
        color: #FFFFFF !important;
        padding: 1rem !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        margin-bottom: 1rem !important;
        box-shadow: 0 4px 10px rgba(239, 68, 68, 0.4) !important;
    }
    .alert-banner-warning {
        background: linear-gradient(90deg, #F59E0B 0%, #D97706 100%) !important;
        color: #FFFFFF !important;
        padding: 1rem !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        margin-bottom: 1rem !important;
    }
    .agent-box {
        background: #1E293B !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
        padding: 1.2rem !important;
        margin-bottom: 1rem !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25) !important;
    }
    .agent-box p {
        color: #F1F5F9 !important;
        font-size: 0.95rem !important;
        line-height: 1.6 !important;
        margin-bottom: 0.4rem !important;
    }
    .agent-box b {
        color: #38BDF8 !important;
    }
    .agent-title {
        color: #38BDF8 !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        border-bottom: 1px solid #334155 !important;
        padding-bottom: 0.4rem !important;
        margin-bottom: 0.6rem !important;
    }

    /* Streamlit Tab Buttons Contrast */
    button[data-baseweb="tab"] {
        font-weight: 700 !important;
        font-size: 0.95rem !important;
    }
    button[data-baseweb="tab"] p {
        color: #94A3B8 !important;
    }
    button[aria-selected="true"] p {
        color: #38BDF8 !important;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.image("https://img.icons8.com/isometric/96/traffic-light.png", width=70)
st.sidebar.markdown(f"## {APP_NAME}")
st.sidebar.caption(f"Version {VERSION} | Multi-Agent CrewAI")

selected_road = st.sidebar.selectbox("📍 Select Junction / Road", ROADS)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎲 Traffic Simulation Mode")

sim_mode = st.sidebar.radio("Simulation Mode", ["Automated Probabilistic", "Manual Scenario Builder"])

if sim_mode == "Manual Scenario Builder":
    st.sidebar.markdown("#### 🎛️ Scenario Parameters")
    man_vehicles = st.sidebar.slider("Vehicle Count", 10, 150, 85)
    man_speed = st.sidebar.slider("Average Speed (km/h)", 10, 80, 25)
    man_weather = st.sidebar.selectbox("Weather Condition", ["Clear", "Rain", "Fog", "Storm"])
    man_accident = st.sidebar.checkbox("⚠️ Report Accident Incident", value=False)
    man_emergency = st.sidebar.checkbox("🚨 Emergency Vehicle Present", value=True)
    man_emerg_type = st.sidebar.selectbox("Emergency Vehicle Type", ["Ambulance", "Fire Truck", "Police Vehicle"]) if man_emergency else None

    if st.sidebar.button("⚡ Run Custom Telemetry Tick", use_container_width=True):
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
        with st.spinner(f"Processing CrewAI pipeline for custom {selected_road} telemetry..."):
            run_traffic_crew(custom_input)
            st.sidebar.success(f"Custom scenario executed for {selected_road}!")
else:
    if st.sidebar.button("⚡ Run Simulation Tick", use_container_width=True):
        with st.spinner("Executing CrewAI 6-Agent Pipeline..."):
            sim_data = TrafficSimulator.generate_random_telemetry(road=selected_road)
            run_traffic_crew(sim_data)
            st.sidebar.success(f"Simulation processed for {selected_road}!")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔊 Voice Broadcast Control")
enable_voice = st.sidebar.toggle("🔊 Enable Audio Announcements", value=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📄 PDF Report Generator")
pdf_bytes_sb = generate_traffic_pdf_report(
    road_name=selected_road,
    reports=reports if 'reports' in locals() else [],
    analytics=get_analytics_summary(limit=20),
    alerts=get_active_alerts(limit=20)
)
st.sidebar.download_button(
    label="📥 Download PDF Summary Report",
    data=pdf_bytes_sb,
    file_name=f"Traffic_Report_{selected_road.replace(' ', '_')}.pdf",
    mime="application/pdf",
    use_container_width=True
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Agent Status")
st.sidebar.markdown("""
- 🟢 **Traffic Monitor**: Online
- 🟢 **Congestion Agent**: Online
- 🟢 **Emergency Agent**: Online
- 🟢 **Smart Weather Agent**: Online 🌧️
- 🟢 **Signal Optimizer**: Online
- 🟢 **Citizen Liaison**: Online
- 🟢 **Analytics Agent**: Online
""")

# Title Header
st.markdown(f"<div class='main-header'>🚦 AI Smart Traffic Management System</div>", unsafe_allow_html=True)
st.markdown(f"<div class='sub-header'>Multi-Agent Autonomous Traffic Optimization Pipeline powered by CrewAI</div>", unsafe_allow_html=True)

# Fetch latest reports & telemetry
reports = get_latest_reports(limit=20)
filtered_reports = [r for r in reports if r["road_name"] == selected_road]

if not filtered_reports:
    # Trigger initial run for road
    sim_data = TrafficSimulator.generate_random_telemetry(road=selected_road)
    run_traffic_crew(sim_data)
    reports = get_latest_reports(limit=20)
    filtered_reports = [r for r in reports if r["road_name"] == selected_road]

latest_report_obj = filtered_reports[0] if filtered_reports else reports[0]
full_report = latest_report_obj.get("full_report", {})

t_rep = full_report.get("traffic_report", {})
c_pred = full_report.get("congestion_prediction", {})
e_corr = full_report.get("emergency_corridor", {})
s_opt = full_report.get("signal_optimization", {})
c_alt = full_report.get("citizen_alerts", {})
a_sum = full_report.get("analytics_summary", {})
w_adapt = full_report.get("weather_adaptation", {})

if not w_adapt:
    from agents.weather_agent import process_weather_rule_based
    w_adapt = process_weather_rule_based(t_rep)

# Emergency Alert Banner & Audio Announcer
if e_corr.get("green_corridor_active"):
    emerg_type = e_corr.get('vehicle_type', 'Emergency Vehicle')
    alert_title = "🚨 GREEN CORRIDOR ACTIVE"
    alert_msg = f"Priority override activated for {emerg_type} on {selected_road}. All intersection signals locked green."
    
    st.markdown(
        f"""
        <div class='alert-banner-emergency'>
            🚨 <b>{alert_title}:</b> Priority override activated for <b>{emerg_type}</b> 
            on <b>{selected_road}</b>. All intersection signals locked green.
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Trigger Voice AI Assistant Announcement & Siren
    voice_html = generate_voice_announcement_html(alert_title, alert_msg, alert_type="EMERGENCY", enabled=enable_voice)
    if voice_html:
        st.components.v1.html(voice_html, height=75)

elif t_rep.get("accident"):
    alert_title = "⚠️ ACCIDENT DETECTED"
    detour_road = c_pred.get('recommended_alternate_roads', ['Service Lane'])[0]
    alert_msg = f"Accident reported on {selected_road}. High delay expected. Detour advised to {detour_road}."
    
    st.markdown(
        f"""
        <div class='alert-banner-warning'>
            ⚠️ <b>{alert_title}:</b> Incident reported on <b>{selected_road}</b>. Detour advised to {detour_road}.
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Trigger Voice AI Assistant Announcement & Chime
    voice_html = generate_voice_announcement_html(alert_title, alert_msg, alert_type="ACCIDENT", enabled=enable_voice)
    if voice_html:
        st.components.v1.html(voice_html, height=75)

if w_adapt.get("weather_condition") in ["Rain", "Storm", "Heavy Rain", "Fog"]:
    w_cond = w_adapt.get("weather_condition").upper()
    st.markdown(
        f"""
        <div class='alert-banner-warning' style='background: linear-gradient(90deg, #0284C7 0%, #1E40AF 100%); margin-top: 10px;'>
            🌧️ <b>SMART WEATHER ADAPTATION ACTIVE ({w_cond}):</b> 
            Speed limit reduced to <b>{w_adapt.get('recommended_speed_limit_kmh')} km/h</b> | 
            Green signal extended <b>+{w_adapt.get('weather_green_extension_sec')}s</b> | 
            Friction index: <b>{w_adapt.get('road_friction_index')}</b>
        </div>
        """,
        unsafe_allow_html=True
    )

# Top KPI Metric Row
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(
        f"""
        <div class='metric-card' style='border-left-color: #3B82F6;'>
            <div class='metric-title'>Vehicle Count</div>
            <div class='metric-value'>{t_rep.get('vehicles', 0)}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    density_color = "#10B981" if t_rep.get("density") == "Low" else ("#F59E0B" if t_rep.get("density") == "Medium" else "#EF4444")
    st.markdown(
        f"""
        <div class='metric-card' style='border-left-color: {density_color};'>
            <div class='metric-title'>Traffic Density</div>
            <div class='metric-value' style='color: {density_color};'>{t_rep.get('density', 'N/A')}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        f"""
        <div class='metric-card' style='border-left-color: #8B5CF6;'>
            <div class='metric-title'>Average Speed</div>
            <div class='metric-value'>{t_rep.get('average_speed', 0)} <span style='font-size: 1rem;'>km/h</span></div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col4:
    c_score = c_pred.get('congestion_score', 0)
    st.markdown(
        f"""
        <div class='metric-card' style='border-left-color: #EC4899;'>
            <div class='metric-title'>Congestion Score</div>
            <div class='metric-value'>{c_score} <span style='font-size: 1rem;'>/ 100</span></div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col5:
    g_time = s_opt.get('recommended_green_time_sec', 30)
    st.markdown(
        f"""
        <div class='metric-card' style='border-left-color: #06B6D4;'>
            <div class='metric-title'>Green Signal</div>
            <div class='metric-value'>{g_time} <span style='font-size: 1rem;'>sec</span></div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)

# Tabs
tab1, tab_vision, tab_driver, tab_gis, tab2, tab3, tab4 = st.tabs([
    "🤖 Multi-Agent Decisions", 
    "👁️ Live YOLOv8 Vision Feed", 
    "🚘 Driver Behavior Analysis", 
    "🗺️ Interactive GIS Map", 
    "🚦 Signal & Corridor Control", 
    "📢 Citizen Broadcast", 
    "📈 Analytics & CO2 Footprint"
])

with tab1:
    st.markdown("### 🤖 Autonomous Agent Pipeline Workflow")
    st.caption("Sequential execution trace across all 6 specialized AI Agents")

    ag1, ag2 = st.columns(2)
    with ag1:
        st.markdown(
            f"""
            <div class='agent-box'>
                <div class='agent-title'>1. Traffic Monitoring Agent</div>
                <p><b>Road:</b> {t_rep.get('road')}</p>
                <p><b>Weather:</b> {t_rep.get('weather')}</p>
                <p><b>Accident:</b> {'Yes ⚠️' if t_rep.get('accident') else 'No 🟢'}</p>
                <p><b>Emergency Vehicle:</b> {'Detected 🚨' if t_rep.get('emergency_vehicle') else 'None'}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class='agent-box'>
                <div class='agent-title'>3. Emergency Vehicle Agent</div>
                <p><b>Priority Status:</b> {e_corr.get('priority_level')}</p>
                <p><b>Green Corridor:</b> {'ACTIVE 🚨' if e_corr.get('green_corridor_active') else 'INACTIVE 🟢'}</p>
                <p><b>Route:</b> {', '.join(e_corr.get('corridor_route', [])) or 'Standard'}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class='agent-box'>
                <div class='agent-title'>5. Citizen Communication Agent</div>
                <p><b>Title:</b> {c_alt.get('title')}</p>
                <p><b>Severity:</b> {c_alt.get('severity')}</p>
                <p><b>Detour Route:</b> {c_alt.get('alternate_route') or 'None required'}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class='agent-box' style='border-left: 4px solid #0284C7;'>
                <div class='agent-title' style='color: #38BDF8;'>7. Smart Weather Adaptability Agent</div>
                <p><b>Weather Condition:</b> {w_adapt.get('weather_condition')}</p>
                <p><b>Speed Limit Adjustment:</b> {w_adapt.get('recommended_speed_limit_kmh')} km/h (-{w_adapt.get('speed_reduction_pct')}%)</p>
                <p><b>Green Time Extension:</b> +{w_adapt.get('weather_green_extension_sec')} sec</p>
                <p><b>Friction Index:</b> {w_adapt.get('road_friction_index')}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with ag2:
        d_safe = t_rep.get("driver_safety", DriverBehaviorTools.evaluate_telemetry(t_rep))
        st.markdown(
            f"""
            <div class='agent-box' style='border-left: 4px solid #F59E0B;'>
                <div class='agent-title' style='color: #F59E0B;'>2. Driver Behavior & Safety Agent</div>
                <p><b>Vehicle ID:</b> {d_safe.get('vehicle_id', 'VH101')}</p>
                <p><b>Safety Score:</b> {d_safe.get('safety_score', 100)} / 100 ({d_safe.get('risk_level', 'LOW')} Risk)</p>
                <p><b>Primary Hazard:</b> {d_safe.get('primary_hazard', 'None')}</p>
                <p><b>Total Violations:</b> {d_safe.get('total_violations', 0)} events</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class='agent-box'>
                <div class='agent-title'>3. Congestion Prediction Agent</div>
                <p><b>Congestion Risk:</b> {c_pred.get('risk_level')}</p>
                <p><b>Predicted Trend:</b> {c_pred.get('predicted_trend')}</p>
                <p><b>Est. Delay:</b> {c_pred.get('estimated_delay_minutes')} mins</p>
                <p><b>Recommended Detours:</b> {', '.join(c_pred.get('recommended_alternate_roads', []))}</p>
            </div>
            """,
            unsafe_allow_html=True
        )


        st.markdown(
            f"""
            <div class='agent-box'>
                <div class='agent-title'>4. Signal Optimization Agent</div>
                <p><b>Control Mode:</b> {s_opt.get('signal_mode')}</p>
                <p><b>Base Green Time:</b> {s_opt.get('current_green_time_sec')} sec</p>
                <p><b>Dynamic Increase:</b> +{s_opt.get('dynamic_increase_sec')} sec</p>
                <p><b>Est. Wait Reduction:</b> {s_opt.get('estimated_wait_time_reduction_pct')}%</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class='agent-box'>
                <div class='agent-title'>6. Analytics Agent</div>
                <p><b>Performance Score:</b> {a_sum.get('road_performance_score')} / 100</p>
                <p><b>Carbon Footprint:</b> {a_sum.get('carbon_emission_kg')} kg CO2</p>
                <p><b>Insights:</b> {a_sum.get('key_insights', ['Normal operations'])[0]}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

with tab_vision:
    st.markdown("### 👁️ Real-Time YOLOv8 CCTV Computer Vision Feed")
    st.caption("Simulated HD video stream with active object bounding boxes, class confidence tags, and camera HUD metrics.")

    vis_col1, vis_col2 = st.columns([3, 1])
    with vis_col1:
        frame_b64 = VisionSimulator.generate_cctv_frame(selected_road, t_rep)
        st.image(frame_b64, caption=f"Live CCTV Camera Node — {selected_road}", use_container_width=True)
    
    with vis_col2:
        st.subheader("YOLO Engine Stats")
        st.metric("Model Architecture", "YOLOv8x-Traffic")
        st.metric("Inference Frame Rate", "30.0 FPS")
        st.metric("Detected Bounding Boxes", t_rep.get("vehicles", 45))
        st.metric("Emergency Priority", "ACTIVE 🚨" if t_rep.get("emergency_vehicle") else "None 🟢")

with tab_driver:
    st.markdown("### 🚘 Driver Behavior & Safety Analytics Engine")
    st.caption("AI telemetry analysis for Sudden Braking, Wrong-Way Driving, Overspeeding, Illegal U-Turns, and Lane Violations with Risk Prediction & Location Intelligence.")

    # Scenario Selection (Telemetry Simulator for Test Cases)
    test_cases = DriverBehaviorTools.get_test_cases()
    tc_names = ["Live Road Telemetry"] + [tc["case_name"] for tc in test_cases]
    selected_scenario = st.selectbox("🧪 Select Telemetry Scenario / Test Case", tc_names, index=0)

    if selected_scenario == "Live Road Telemetry":
        # Extract driver safety report from crew execution or generate dynamically
        if "driver_safety" in t_rep:
            driver_eval = t_rep["driver_safety"]
        else:
            driver_eval = DriverBehaviorTools.evaluate_telemetry(t_rep)
    else:
        # Find matching test case payload
        matched_tc = next(tc for tc in test_cases if tc["case_name"] == selected_scenario)
        driver_eval = DriverBehaviorTools.evaluate_telemetry(matched_tc["telemetry"])

    v_breakdown = driver_eval.get("violations", {})
    risk_pred = driver_eval.get("risk_prediction", {})
    loc_intel = driver_eval.get("location_intelligence", {})
    score = driver_eval.get("safety_score", 100)
    risk_lvl = driver_eval.get("risk_level", "LOW")

    # Driver Safety Index & Gauge
    col_d1, col_d2 = st.columns([1, 2])
    with col_d1:
        st.subheader("Driver Safety Index")
        status_color = "#10B981" if risk_lvl == "LOW" else ("#F59E0B" if risk_lvl == "MEDIUM" else ("#F97316" if risk_lvl == "HIGH" else "#EF4444"))
        
        st.markdown(
            f"""
            <div style='background-color: #1E293B; border-left: 5px solid {status_color}; padding: 12px; border-radius: 8px; margin-bottom: 12px;'>
                <p style='margin: 0; font-size: 0.9rem; color: #94A3B8;'>CURRENT STATUS & RISK LEVEL</p>
                <p style='margin: 0; font-size: 1.3rem; font-weight: 700; color: {status_color};'>{risk_lvl} RISK LEVEL ({score}/100)</p>
                <p style='margin: 4px 0 0 0; font-size: 0.85rem; color: #E2E8F0;'>Reason: {driver_eval.get('primary_hazard', 'Normal Flow')}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        fig_safety = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            title={'text': f"Vehicle ID: {driver_eval.get('vehicle_id', 'VH101')}"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': status_color},
                'steps': [
                    {'range': [0, 39], 'color': "#7F1D1D"},
                    {'range': [40, 59], 'color': "#431407"},
                    {'range': [60, 79], 'color': "#451A03"},
                    {'range': [80, 100], 'color': "#064E3B"}
                ]
            }
        ))
        fig_safety.update_layout(
            template="plotly_dark",
            height=250,
            margin=dict(l=20, r=20, t=40, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#F8FAFC", family="Inter, sans-serif")
        )
        st.plotly_chart(fig_safety, use_container_width=True)

    with col_d2:
        st.subheader("Detected Driving Violations Breakdown")
        
        vk1, vk2, vk3 = st.columns(3)
        with vk1:
            st.markdown(
                f"""
                <div class='metric-card' style='border-left-color: #EF4444;'>
                    <div class='metric-title'>🛑 Sudden Braking</div>
                    <div class='metric-value'>{v_breakdown.get('sudden_braking', 0)} <span style='font-size: 1rem;'>events</span></div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with vk2:
            st.markdown(
                f"""
                <div class='metric-card' style='border-left-color: #F59E0B;'>
                    <div class='metric-title'>⛔ Wrong-Way Driving</div>
                    <div class='metric-value'>{v_breakdown.get('wrong_way', 0)} <span style='font-size: 1rem;'>incidents</span></div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with vk3:
            st.markdown(
                f"""
                <div class='metric-card' style='border-left-color: #38BDF8;'>
                    <div class='metric-title'>⚡ Overspeeding</div>
                    <div class='metric-value'>{v_breakdown.get('overspeeding', 0)} <span style='font-size: 1rem;'>vehicles</span></div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("<br>", unsafe_allow_html=True)
        vk4, vk5, vk6 = st.columns(3)
        with vk4:
            st.markdown(
                f"""
                <div class='metric-card' style='border-left-color: #A855F7;'>
                    <div class='metric-title'>↩️ Illegal U-Turns</div>
                    <div class='metric-value'>{v_breakdown.get('illegal_u_turn', 0)} <span style='font-size: 1rem;'>events</span></div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with vk5:
            st.markdown(
                f"""
                <div class='metric-card' style='border-left-color: #10B981;'>
                    <div class='metric-title'>🛣️ Lane Violations</div>
                    <div class='metric-value'>{v_breakdown.get('lane_violations', 0)} <span style='font-size: 1rem;'>drifts</span></div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with vk6:
            st.markdown(
                f"""
                <div class='metric-card' style='border-left-color: #EC4899;'>
                    <div class='metric-title'>📊 Total Violations</div>
                    <div class='metric-value'>{driver_eval.get('total_violations', 0)} <span style='font-size: 1rem;'>total</span></div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("<hr style='border-color: #1E293B;'>", unsafe_allow_html=True)

    # Innovative Feature & Location Intelligence
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.subheader("🔮 Driver Risk Prediction Engine")
        pred_badge_color = "#EF4444" if risk_pred.get("probability") == "HIGH" else ("#F59E0B" if risk_pred.get("probability") == "MODERATE" else "#10B981")
        st.markdown(
            f"""
            <div style='background-color: #111827; border: 1px solid #374151; padding: 16px; border-radius: 8px;'>
                <p style='margin: 0 0 6px 0; font-size: 0.9rem; color: #9CA3AF;'>FUTURE UNSAFE DRIVING PROBABILITY</p>
                <span style='background-color: {pred_badge_color}; color: #FFFFFF; font-weight: 700; padding: 4px 10px; border-radius: 12px;'>{risk_pred.get('probability', 'LOW')} PROBABILITY</span>
                <p style='margin: 12px 0 6px 0; font-size: 1rem; color: #F3F4F6; font-weight: 600;'>"{risk_pred.get('statement', '')}"</p>
                <p style='margin: 0; font-size: 0.9rem; color: #38BDF8;'><strong>Preventive Action:</strong> {risk_pred.get('preventive_action', '')}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_p2:
        st.subheader("📍 Location Intelligence & Violation Hotspot")
        gps = driver_eval.get("location", {})
        st.markdown(
            f"""
            <div style='background-color: #111827; border: 1px solid #374151; padding: 16px; border-radius: 8px;'>
                <p style='margin: 0 0 6px 0; font-size: 0.9rem; color: #9CA3AF;'>GEOSPATIAL COORDINATES</p>
                <p style='margin: 0; font-size: 1.05rem; font-weight: 700; color: #F3F4F6;'>Road ID: {driver_eval.get('road_id', 'Main Road')}</p>
                <p style='margin: 4px 0; font-size: 0.95rem; color: #E5E7EB;'>Latitude: {gps.get('latitude', 13.0827)}, Longitude: {gps.get('longitude', 80.2707)}</p>
                <p style='margin: 4px 0 0 0; font-size: 0.9rem; color: #A855F7;'><strong>Zone Classification:</strong> {loc_intel.get('zone_classification', 'Standard Corridor')}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("#### 🚨 Safety Intelligence Audit Alerts")
    st.code(driver_eval.get("formatted_alert", ""), language="text")


with tab_gis:
    st.markdown("### 🗺️ Live GIS & Google Maps Visualizer")
    st.caption("Real-time geospatial visualization powered by Google Maps Tiles, Folium, and PyDeck 3D engines.")

    gis_engine = st.radio("Select GIS Map View Engine", ["🗺️ Google Maps (Real Streets & Satellite + Live Links)", "📊 PyDeck 3D Elevation Pillars"], horizontal=True)

    map_data = []
    recent_reports = get_latest_reports(limit=25)
    
    # Map latest report per road
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

        # Color coding
        if has_emerg:
            color_rgb = [239, 68, 68, 255] # Red
            color_hex = "#EF4444"
            status_text = "🚨 EMERGENCY CORRIDOR ACTIVE"
        elif has_acc:
            color_rgb = [245, 158, 11, 255] # Orange
            color_hex = "#F59E0B"
            status_text = "⚠️ ACCIDENT DETECTED"
        elif density == "Low":
            color_rgb = [16, 185, 129, 200] # Green
            color_hex = "#10B981"
            status_text = "🟢 Low Density (Smooth Flow)"
        elif density == "Medium":
            color_rgb = [245, 158, 11, 200] # Amber
            color_hex = "#F59E0B"
            status_text = "🟡 Medium Density"
        else:
            color_rgb = [239, 68, 68, 220] # Red
            color_hex = "#EF4444"
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
        st.markdown("#### 🛰️ Google Maps Satellite & Hybrid Road Map Layer")
        
        # Initialize Folium Map centered at City Center
        m = folium.Map(
            location=[12.9720, 77.5950],
            zoom_start=13,
            tiles=None
        )

        # Add Google Maps Street Tiles Layer
        folium.TileLayer(
            tiles="http://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
            attr="Google Maps Streets",
            name="Google Streets",
            overlay=False,
            control=True
        ).add_to(m)

        # Add Google Maps Satellite Layer
        folium.TileLayer(
            tiles="http://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
            attr="Google Maps Hybrid Satellite",
            name="Google Satellite (Hybrid)",
            overlay=False,
            control=True
        ).add_to(m)

        # Add Layer Control
        folium.LayerControl().add_to(m)

        # Add Junction Markers
        for row in map_data:
            popup_html = f"""
            <div style="font-family: 'Inter', sans-serif; width: 220px; background-color: #0F172A; color: #F8FAFC; padding: 12px; border-radius: 8px; border: 1px solid #334155;">
                <h4 style="margin: 0 0 6px 0; color: #38BDF8;">📍 {row['road']}</h4>
                <p style="margin: 3px 0; color: #E2E8F0;"><b>Status:</b> {row['status_text']}</p>
                <p style="margin: 3px 0; color: #E2E8F0;"><b>Vehicles:</b> {row['vehicles']} cars</p>
                <p style="margin: 3px 0; color: #E2E8F0;"><b>Average Speed:</b> {row['speed']} km/h</p>
                <hr style="margin: 8px 0; border: 0; border-top: 1px solid #334155;">
                <a href="{row['gmaps_url']}" target="_blank" 
                   style="background: #0284C7; color: #FFFFFF; padding: 6px 12px; border-radius: 4px; text-decoration: none; display: inline-block; font-weight: bold; font-size: 12px;">
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

        # Display Folium Map in Streamlit
        st_folium(m, width="100%", height=480)

        # Direct Google Maps Links Bar
        st.markdown("#### 🔗 Direct Google Maps Junction Links")
        link_cols = st.columns(len(map_data))
        for idx, row in enumerate(map_data):
            with link_cols[idx]:
                st.markdown(f"[{row['road']}]({row['gmaps_url']})")

    else:
        # PyDeck Map Engine
        st.markdown("#### 📊 PyDeck 3D Traffic Density Pillars Map")
        view_state = pdk.ViewState(
            latitude=12.9720,
            longitude=77.5950,
            zoom=12.5,
            pitch=45.0,
            bearing=15.0
        )

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
            map_style="mapbox://styles/mapbox/dark-v10",
            tooltip={"text": "{road}\nDensity: {density}\nVehicles: {vehicles}\nStatus: {status_text}"}
        )

        st.pydeck_chart(deck, use_container_width=True)

    # GIS Legend Row
    st.markdown("#### 🔑 GIS Map Legend")
    lg1, lg2, lg3, lg4 = st.columns(4)
    with lg1:
        st.markdown("🟢 **Low Density**: Smooth flow (<45 vehicles)")
    with lg2:
        st.markdown("🟡 **Medium Density**: Moderate traffic (45-75 vehicles)")
    with lg3:
        st.markdown("🔴 **High / Critical Density**: Heavy traffic (>75 vehicles)")
    with lg4:
        st.markdown("🚨 **Pulsing Marker**: Active Emergency Green Corridor")

with tab2:
    st.markdown("### 🚦 Junction Signal Control & Emergency Corridor")
    st.caption("Real-time Cyber-Physical Signal Controller & First-Responder Priority Override")

    col_sig1, col_sig2 = st.columns([1, 2])
    with col_sig1:
        st.subheader("Signal Mode & Gauge")
        st.info(f"**Current Mode:** {s_opt.get('signal_mode', 'Standard')}")
        
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=s_opt.get('recommended_green_time_sec', 30),
            title={'text': "Recommended Green Light (Sec)"},
            gauge={
                'axis': {'range': [0, 120]},
                'bar': {'color': "#10B981"},
                'steps': [
                    {'range': [0, 35], 'color': "#1E293B"},
                    {'range': [35, 75], 'color': "#334155"},
                    {'range': [75, 120], 'color': "#0F172A"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig_gauge.update_layout(
            template="plotly_dark",
            height=260,
            margin=dict(l=20, r=20, t=40, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#F8FAFC", family="Inter, sans-serif")
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_sig2:
        st.subheader("Intersections Grid Signal Status")
        junction_data = []
        for r_name in ROADS:
            is_active_road = (r_name == selected_road)
            g_sec = s_opt.get('recommended_green_time_sec', 30) if is_active_road else 30
            mode = s_opt.get('signal_mode', 'Standard') if is_active_road else "Standard-Balanced"
            junction_data.append({
                "Junction / Road": r_name,
                "Signal Mode": mode,
                "Green Phase (sec)": g_sec,
                "Wait Time Reduction": f"{s_opt.get('estimated_wait_time_reduction_pct', 10.0)}%" if is_active_road else "10.0%",
                "Status": "🚨 Green Corridor Lock" if (is_active_road and e_corr.get("green_corridor_active")) else "🟢 Adaptive Cycle"
            })
        st.dataframe(pd.DataFrame(junction_data), use_container_width=True)

        st.markdown("#### ⚡ Manual Signal Controls & Emergency Override")
        ctrl_col1, ctrl_col2 = st.columns(2)
        with ctrl_col1:
            if st.button("🚨 Force Emergency Green Corridor", use_container_width=True):
                emergency_override_input = {
                    "road": selected_road,
                    "vehicle_count": 85,
                    "average_speed": 20.0,
                    "road_occupancy_pct": 80.0,
                    "accident": False,
                    "emergency_vehicle": True,
                    "emergency_type": "Ambulance",
                    "weather": "Clear"
                }
                run_traffic_crew(emergency_override_input)
                st.success(f"Green Corridor forcefully locked for {selected_road}!")
                st.rerun()
        with ctrl_col2:
            if st.button("🔄 Reset to Standard Adaptive Mode", use_container_width=True):
                normal_input = {
                    "road": selected_road,
                    "vehicle_count": 35,
                    "average_speed": 55.0,
                    "road_occupancy_pct": 35.0,
                    "accident": False,
                    "emergency_vehicle": False,
                    "emergency_type": None,
                    "weather": "Clear"
                }
                run_traffic_crew(normal_input)
                st.success(f"Signal reset to standard adaptive mode for {selected_road}!")
                st.rerun()

with tab3:
    st.markdown("### 📢 Citizen Alerts & Public Broadcasts")
    st.caption("Multi-channel citizen traffic alert system with instant WhatsApp dispatch & VMS sign board integration.")

    col_bcast1, col_bcast2 = st.columns([3, 2])

    with col_bcast1:
        st.subheader("📋 Active System Alerts Log")
        alerts_list = get_active_alerts(limit=15)
        if alerts_list:
            df_alerts = pd.DataFrame(alerts_list)[["timestamp", "severity", "title", "road_name", "message", "alternate_route"]]
            st.dataframe(df_alerts, use_container_width=True)
        else:
            st.info("No active alerts currently broadcasted.")

    with col_bcast2:
        st.subheader("📲 WhatsApp Traffic Alert Dispatcher")
        st.markdown("Send real-time traffic status, emergency corridor alerts, or detour directions directly to any citizen WhatsApp number.")

        wa_phone = st.text_input("📱 Recipient WhatsApp Number (with Country Code)", value="+919876543210", help="e.g. +919876543210 or +15551234567")
        
        # Build default alert template based on active state
        default_title = c_alt.get("title", f"Traffic Update for {selected_road}")
        default_severity = c_alt.get("severity", "INFO")
        default_message = c_alt.get("message", f"Traffic is flowing on {selected_road}.")
        default_alternate = c_alt.get("alternate_route", "N/A")

        title_input = st.text_input("Headline Title", value=default_title)
        severity_input = st.selectbox("Severity Level", ["EMERGENCY", "CRITICAL", "WARNING", "INFO"], index=["EMERGENCY", "CRITICAL", "WARNING", "INFO"].index(default_severity) if default_severity in ["EMERGENCY", "CRITICAL", "WARNING", "INFO"] else 3)
        message_input = st.text_area("Alert Message Text", value=default_message, height=90)
        alternate_input = st.text_input("Advised Detour Route", value=default_alternate if default_alternate else "N/A")

        # Format message template
        formatted_wa_msg = WhatsAppNotifier.format_whatsapp_message(
            title=title_input,
            severity=severity_input,
            message=message_input,
            road=selected_road,
            alternate_route=alternate_input
        )

        st.markdown("#### 💬 WhatsApp Broadcast Preview")
        st.code(formatted_wa_msg, language="markdown")

        if st.button("📲 Dispatch WhatsApp Traffic Alert", use_container_width=True):
            if not wa_phone or len(wa_phone) < 8:
                st.error("Please enter a valid WhatsApp phone number with country code.")
            else:
                # Try Twilio API if keys present
                twilio_success, twilio_msg = WhatsAppNotifier.send_via_twilio(wa_phone, formatted_wa_msg)
                
                # Generate Click-to-Chat Link
                wa_web_link = WhatsAppNotifier.generate_whatsapp_web_link(wa_phone, formatted_wa_msg)
                
                if twilio_success:
                    st.success(f"✅ {twilio_msg}")
                else:
                    st.info(f"ℹ️ {twilio_msg}")

                st.markdown(
                    f"""
                    <div style="margin-top: 10px; text-align: center;">
                        <a href="{wa_web_link}" target="_blank" 
                           style="background-color: #25D366; color: white; padding: 10px 20px; border-radius: 8px; font-weight: bold; text-decoration: none; display: inline-block; font-size: 14px;">
                           💬 Open & Send in WhatsApp App / Web
                        </a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

with tab4:
    st.markdown("### 📈 Historical Analytics & Sustainability Report")
    
    col_pdf1, col_pdf2 = st.columns([3, 1])
    with col_pdf1:
        st.caption("City-wide vehicle flow stats, peak traffic trends, and carbon reduction metrics.")
    with col_pdf2:
        pdf_data = generate_traffic_pdf_report(
            road_name=selected_road,
            reports=reports,
            analytics=get_analytics_summary(limit=30),
            alerts=get_active_alerts(limit=30)
        )
        st.download_button(
            label="📥 Export Printable PDF Report",
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
                title="Congestion Score Trend Over Time",
                markers=True
            )
            fig_cong.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#F8FAFC", family="Inter, sans-serif"),
                xaxis=dict(gridcolor="#334155"),
                yaxis=dict(gridcolor="#334155")
            )
            st.plotly_chart(fig_cong, use_container_width=True)

        with c_graph2:
            fig_co2 = px.bar(
                df_analytics,
                x="road_name",
                y="carbon_emission_kg",
                color="congestion_index",
                title="Carbon Emission (CO2 kg) by Road",
                color_continuous_scale="Reds"
            )
            fig_co2.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#F8FAFC", family="Inter, sans-serif"),
                xaxis=dict(gridcolor="#334155"),
                yaxis=dict(gridcolor="#334155")
            )
            st.plotly_chart(fig_co2, use_container_width=True)
    else:
        st.info("Run simulation ticks to populate analytics graphs.")
