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


@tool("Fetch Latest Telemetry Tool")
def fetch_telemetry_tool(road_name: str) -> str:
    """Fetches recent traffic telemetry data from SQLite database for a specific road."""
    records = get_latest_traffic_data(limit=5)
    filtered = [r for r in records if r["road"].lower() == road_name.lower()]
    if not filtered:
        return json.dumps({"status": "No historical data found", "road": road_name})
    return json.dumps(filtered[0])


@tool("Fetch Active Alerts Tool")
def fetch_alerts_tool(road_name: str) -> str:
    """Fetches active emergency and citizen alerts for a road."""
    alerts = get_active_alerts(limit=5)
    filtered = [a for a in alerts if road_name.lower() in a["road_name"].lower()]
    return json.dumps(filtered)
