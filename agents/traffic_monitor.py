"""
Agent 1: Traffic Monitoring Agent
Monitors city traffic telemetry, validates metrics, and generates standardized Traffic Reports.
"""

import json
import logging
from typing import Dict, Any

try:
    from crewai import Agent
except Exception:
    Agent = None

from config.settings import get_llm
from tools.traffic_data_fetcher import fetch_traffic_data, TrafficDataFetcher

logger = logging.getLogger("smart_traffic_ai.agent.traffic_monitor")


def create_traffic_monitor_agent() -> Agent:
    """Factory to create CrewAI Traffic Monitoring Agent with fetch_traffic_data tool."""
    if Agent is None:
        return None
    llm = get_llm()
    return Agent(
        role="Traffic Monitoring Agent",
        goal="Monitor city traffic telemetry continuously, validate metrics, and generate standard structured JSON Traffic Reports.",
        backstory=(
            "You are the Chief AI Traffic Monitoring Officer at the Smart City Command Hub. "
            "Your job is to fetch real-time structured traffic metrics (road_id, road_name, latitude, longitude, vehicle_count, "
            "average_speed, traffic_density, congestion_level, travel_time, normal_travel_time, delay, accident_status, "
            "emergency_vehicle_status, road_status, weather, timestamp) using your tools. "
            "You MUST NEVER hallucinate or invent traffic values. If a field is unavailable, label it 'unavailable'. "
            "Generate structured JSON Traffic Reports for all downstream agents."
        ),
        tools=[fetch_traffic_data],
        verbose=True,
        memory=True,
        llm=llm
    )


def process_traffic_monitor_rule_based(telemetry: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic, validated execution engine for Traffic Monitoring Agent."""
    road = telemetry.get("road_name", telemetry.get("road", "Main Road"))
    
    # If telemetry is sparse, enrich via TrafficDataFetcher
    if not telemetry.get("road_id") or "travel_time" not in telemetry:
        fetched = TrafficDataFetcher.get_traffic_data(road)
        # Merge telemetry inputs over fetched defaults if provided
        for k, v in telemetry.items():
            if k in ["vehicle_count", "vehicles", "average_speed", "accident", "emergency_vehicle", "weather"]:
                if k == "vehicles":
                    fetched["vehicle_count"] = v
                elif k == "accident":
                    fetched["accident_status"] = bool(v)
                elif k == "emergency_vehicle":
                    fetched["emergency_vehicle_status"] = bool(v)
                else:
                    fetched[k] = v
        struct_data = fetched
    else:
        struct_data = telemetry

    # Formulate structured agent output
    vehicles = struct_data.get("vehicle_count", 50)
    speed = struct_data.get("average_speed", 40.0)
    density = str(struct_data.get("traffic_density", "MEDIUM")).title()
    if density.lower() not in ["low", "medium", "high", "critical"]:
        density = "Medium"

    logger.info(f"[AGENT] Traffic analysis completed for {road}. Density: {density}, Vehicles: {vehicles}")

    return {
        "road_id": struct_data.get("road_id", "R001"),
        "road": road,
        "road_name": road,
        "location": {
            "latitude": struct_data.get("latitude", 13.0827),
            "longitude": struct_data.get("longitude", 80.2707)
        },
        "vehicles": vehicles if isinstance(vehicles, int) else 50,
        "vehicle_count": vehicles,
        "average_speed": speed if isinstance(speed, (int, float)) else 40.0,
        "traffic_density": density.upper(),
        "density": density,
        "congestion_level": struct_data.get("congestion_level", 40),
        "travel_time": struct_data.get("travel_time", 15),
        "normal_travel_time": struct_data.get("normal_travel_time", 10),
        "delay": struct_data.get("delay", 5),
        "accident": bool(struct_data.get("accident_status", False)),
        "accident_status": bool(struct_data.get("accident_status", False)),
        "emergency_vehicle": bool(struct_data.get("emergency_vehicle_status", False)),
        "emergency_vehicle_status": bool(struct_data.get("emergency_vehicle_status", False)),
        "road_status": str(struct_data.get("road_status", "OPEN")).upper(),
        "weather": str(struct_data.get("weather", "CLEAR")).upper(),
        "timestamp": struct_data.get("timestamp", ""),
        "risk_level": "HIGH" if struct_data.get("congestion_level", 0) > 70 or struct_data.get("accident_status") else "MEDIUM"
    }
