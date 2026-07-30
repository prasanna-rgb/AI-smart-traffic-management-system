"""
CrewAI Custom Tools for Database Interactions.
"""
import json
try:
    from crewai.tools import tool
except Exception:
    def tool(name: str):
        def decorator(func):
            return func
        return decorator
from database.db import get_latest_traffic_data, get_latest_reports, get_active_alerts
from tools.live_traffic_api import fetch_live_traffic_telemetry


@tool("Fetch Latest Telemetry Tool")
def fetch_telemetry_tool(road_name: str) -> str:
    """Fetches real-time traffic & weather telemetry data from Live APIs for a specific road."""
    records = get_latest_traffic_data(limit=5)
    filtered = [r for r in records if r["road"].lower() == road_name.lower()]
    if filtered:
        return json.dumps(filtered[0])
    
    # Live Real-Time API fallback
    live_data = fetch_live_traffic_telemetry(road_name)
    return json.dumps(live_data)


@tool("Fetch Active Alerts Tool")
def fetch_alerts_tool(road_name: str) -> str:
    """Fetches active emergency and citizen alerts for a road."""
    alerts = get_active_alerts(limit=5)
    filtered = [a for a in alerts if road_name.lower() in a["road_name"].lower()]
    return json.dumps(filtered)
