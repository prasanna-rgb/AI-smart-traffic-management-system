"""
Agent 1: Traffic Monitoring Agent
Monitors city traffic telemetry, computes density levels, and generates standardized Traffic Reports.
"""
import json
from typing import Dict, Any
try:
    from crewai import Agent
except Exception:
    Agent = None
from config.settings import get_llm
from tools.database_tools import fetch_telemetry_tool


def create_traffic_monitor_agent() -> Agent:
    """Factory to create CrewAI Traffic Monitoring Agent."""
    llm = get_llm()
    return Agent(
        role="Traffic Monitoring Agent",
        goal="Monitor city traffic telemetry continuously and generate standard JSON Traffic Reports.",
        backstory=(
            "You are an expert AI traffic observer at the Smart City Command Hub. "
            "Your job is to read raw telemetry (vehicle count, speed, road occupancy, accidents, weather, emergency vehicles) "
            "and produce structured, precise traffic reports with accurate density classification (Low, Medium, High, Critical)."
        ),
        tools=[fetch_telemetry_tool],
        verbose=True,
        memory=True,
        llm=llm
    )


def process_traffic_monitor_rule_based(telemetry: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic fallback logic for Traffic Monitoring Agent."""
    road = telemetry.get("road", "Main Road")
    vehicles = telemetry.get("vehicle_count", telemetry.get("vehicles", 50))
    speed = telemetry.get("average_speed", 40.0)
    occupancy = telemetry.get("road_occupancy_pct", 50.0)
    accident = telemetry.get("accident", False)
    emergency = telemetry.get("emergency_vehicle", False)
    emergency_type = telemetry.get("emergency_type")
    weather = telemetry.get("weather", "Clear")

    # Compute density
    if accident or occupancy > 85.0 or (vehicles > 90 and speed < 25):
        density = "Critical"
    elif occupancy > 70.0 or vehicles > 75 or speed < 30:
        density = "High"
    elif occupancy > 45.0 or vehicles > 45:
        density = "Medium"
    else:
        density = "Low"

    return {
        "road": road,
        "vehicles": vehicles,
        "density": density,
        "average_speed": speed,
        "accident": accident,
        "emergency_vehicle": emergency,
        "emergency_type": emergency_type,
        "weather": weather
    }
