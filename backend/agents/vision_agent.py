"""
Vision Agent: Ingests video & camera frame detections, extracts vehicle composition metrics.
"""
from typing import Dict, Any
from config.settings import get_llm

try:
    from crewai import Agent
    CREWAI_AVAILABLE = True
except Exception:
    CREWAI_AVAILABLE = False
    Agent = None

def create_vision_agent():
    if not CREWAI_AVAILABLE:
        return None
    llm = get_llm()
    return Agent(
        role="Computer Vision & Traffic Stream Monitoring Specialist",
        goal="Extract accurate vehicle classification counts (cars, buses, trucks, motorcycles, ambulances) and real-time density metrics from camera feeds.",
        backstory="""You are an expert AI Computer Vision Engineer trained on YOLOv8 and traffic stream analysis.
        Your job is to convert pixel detections into clean structured vehicle telemetry, identifying emergency vehicles and density levels.""",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

def process_vision_rule_based(telemetry: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic rule engine for Vision Agent processing."""
    car = telemetry.get("car", telemetry.get("vehicles", 35))
    bus = telemetry.get("bus", 3)
    truck = telemetry.get("truck", 2)
    motorcycle = telemetry.get("motorcycle", 8)
    ambulance = telemetry.get("ambulance", 1 if telemetry.get("emergency_vehicle") else 0)

    total_vehicles = car + bus + truck + motorcycle + ambulance
    avg_speed = telemetry.get("average_speed", max(10.0, 60.0 - (total_vehicles * 0.8)))
    density_pct = min(100.0, round((total_vehicles / 45.0) * 100.0, 1))

    density_category = "Low"
    if density_pct > 75:
        density_category = "Critical"
    elif density_pct > 55:
        density_category = "High"
    elif density_pct > 30:
        density_category = "Medium"

    return {
        "intersection_code": telemetry.get("intersection_code", telemetry.get("road", "INT-01")),
        "timestamp": telemetry.get("timestamp"),
        "total_vehicles": total_vehicles,
        "fleet_breakdown": {
            "car": car,
            "bus": bus,
            "truck": truck,
            "motorcycle": motorcycle,
            "ambulance": ambulance
        },
        "average_speed_kmh": round(avg_speed, 1),
        "density_pct": density_pct,
        "density_category": density_category,
        "emergency_vehicle_detected": ambulance > 0 or telemetry.get("emergency_vehicle", False)
    }
