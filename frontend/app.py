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

st.sidebar.markdown("---")
st.sidebar.markdown("### 📱 Registered Commuter Phone Number")
reg_phone = st.sidebar.text_input("Mobile Number for AI Auto-Alerts", value="+916383258373", help="When Emergency, Accident, or Congestion >70 trigger automatically, AI dispatches WhatsApp & SMS to this number!")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🌐 Data Source Engine")
sim_mode = st.sidebar.radio("Telemetry Data Source", ["🌐 Live Real-Time API Data Feed (Open-Meteo & Live GPS)", "Manual Scenario Injection"])

if sim_mode == "Manual Scenario Injection":
    st.sidebar.markdown("#### Scenario Parameters")
    man_vehicles = st.sidebar.slider("Vehicle Density (cars/hr)", 10, 150, 85)
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
            run_traffic_crew(custom_input, registered_phone=reg_phone)
            st.sidebar.success(f"Custom telemetry frame processed for {selected_road}")
else:
    st.sidebar.caption("🌐 Currently pulling live real-time weather & traffic telemetry via Open-Meteo API & OpenStreetMap GPS coordinates.")
    if st.sidebar.button("⚡ Fetch Live Real-Time API Feed & Run Agents", use_container_width=True):
        with st.spinner("Fetching Live API data & executing CrewAI Multi-Agent Pipeline..."):
            sim_data = TrafficSimulator.generate_random_telemetry(road=selected_road)
            run_traffic_crew(sim_data, registered_phone=reg_phone)
            st.sidebar.success(f"Live API data fetched for {selected_road}!")

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
- 🟢 **Congestion Prediction Agent**: Active
- 🟢 **Emergency Vehicle Agent**: Active
- 🟢 **Signal Optimization Agent**: Active
- 🟢 **Citizen Liaison Agent**: Active
- 🟢 **Analytics Agent**: Active
- 🟢 **V2I Pre-Crash Agent**: Active
""")

# Fetch latest reports & telemetry
reports = get_latest_reports(limit=20)
filtered_reports = [r for r in reports if r["road_name"] == selected_road]

if not filtered_reports:
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

# Emergency Alert Banners & Audio Announcements
if e_corr.get("green_corridor_active"):
    emerg_type = e_corr.get('vehicle_type', 'Emergency Vehicle')
    alert_title = "🚨 EMERGENCY GREEN CORRIDOR ACTIVE"
    alert_msg = f"Priority override active for {emerg_type} on {selected_road}. All intersection signals locked green."
    
    st.markdown(
        f"""
        <div class='banner-critical'>
            <b>🚨 EMERGENCY GREEN CORRIDOR ACTIVE:</b> Signal override locked for <b>{emerg_type}</b> on <b>{selected_road}</b>. Intersections cleared.
        </div>
        """,
        unsafe_allow_html=True
    )
    
    voice_html = generate_voice_announcement_html(alert_title, alert_msg, enabled=enable_voice)
    if voice_html:
        st.components.v1.html(voice_html, height=0)

elif t_rep.get("accident"):
    alert_title = "⚠️ TRAFFIC INCIDENT DETECTED"
    detour_road = c_pred.get('recommended_alternate_roads', ['Service Lane'])[0]
    alert_msg = f"Accident reported on {selected_road}. Detour advised via {detour_road}."
    
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
            <div class='metric-head'>Vehicle Flow Rate</div>
            <div class='metric-body'>{t_rep.get('vehicles', 0)}</div>
            <div class='metric-sub'>vehicles / hour</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    density_val = t_rep.get("density", "N/A")
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
            <div class='metric-body'>{t_rep.get('average_speed', 0)}</div>
            <div class='metric-sub'>km / hour</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col4:
    c_score = c_pred.get('congestion_score', 0)
    st.markdown(
        f"""
        <div class='metric-box'>
            <div class='metric-head'>Congestion Index</div>
            <div class='metric-body' style='color: #DB2777;'>{c_score}</div>
            <div class='metric-sub'>scale 0 to 100</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col5:
    g_time = s_opt.get('recommended_green_time_sec', 30)
    st.markdown(
        f"""
        <div class='metric-box'>
            <div class='metric-head'>Green Phase Target</div>
            <div class='metric-body' style='color: #2563EB;'>{g_time}</div>
            <div class='metric-sub'>seconds duration</div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)

# Main Navigation Tabs
tab1, tab_gis, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Executive Operations & Agent Flow", 
    "🗺️ GIS Map & Google Satellite", 
    "🚦 Signal Controllers & Preemption", 
    "📢 Citizen Broadcast Feed", 
    "📈 Analytics & Sustainability",
    "🛡️ V2I Pre-Crash Safety"
])

# Extract new agent data
v2i = full_report.get("v2i_precrash", {})

with tab1:
    st.markdown("#### 🤖 CrewAI Multi-Agent Execution Trace")
    st.caption("Real-time decision pipeline across 7 specialized autonomous agents")

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
                <div class='agent-title-text' style='color: #DC2626;'>3. Emergency Vehicle Agent</div>
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
                <div class='agent-title-text' style='color: #059669;'>5. Citizen Communication Agent</div>
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
    st.markdown("#### 🚦 Signal Controllers & Intersection Preemption")

    col_sig1, col_sig2 = st.columns([1, 2])
    with col_sig1:
        st.subheader("Signal Mode")
        st.info(f"**Current Mode:** {s_opt.get('signal_mode', 'Standard')}")
        
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=s_opt.get('recommended_green_time_sec', 30),
            title={'text': "Green Light Duration (Sec)"},
            gauge={
                'axis': {'range': [0, 120]},
                'bar': {'color': "#2563EB"},
                'steps': [
                    {'range': [0, 35], 'color': "#F1F5F9"},
                    {'range': [35, 75], 'color': "#E2E8F0"},
                    {'range': [75, 120], 'color': "#CBD5E1"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig_gauge.update_layout(height=280, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_sig2:
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
            reports=reports,
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

