"""
Agent 3: Emergency Vehicle Agent
Classifies emergency events (Accident, Medical, Fire, Police, Critical),
plans Green Corridors, and overrides signal cycles.
"""
import json
import logging
from typing import Dict, Any

try:
    from crewai import Agent
except Exception:
    Agent = None

from config.settings import get_llm

logger = logging.getLogger("smart_traffic_ai.agent.emergency")


def create_emergency_agent() -> Agent:
    """Factory to create CrewAI Emergency Vehicle Agent."""
    if Agent is None:
        return None
    llm = get_llm()
    return Agent(
        role="Emergency Vehicle Management Agent",
        goal="Classify emergency events, calculate zero-wait Green Corridors via Google Maps routing, and lock signals along emergency corridors.",
        backstory=(
            "You are a Priority Emergency Dispatch AI specializing in life-safety routing and incident response. "
            "When an accident or emergency vehicle (Ambulance, Fire Truck, Police) is detected, you classify the severity, "
            "calculate optimal green corridor routes, and command signal nodes to preempt standard traffic light cycles."
        ),
        verbose=True,
        memory=True,
        llm=llm
    )


def process_emergency_rule_based(traffic_report: Dict[str, Any], congestion_info: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic, safety-checked execution engine for Emergency Vehicle Agent."""
    road = traffic_report.get("road_name", traffic_report.get("road", "Main Road"))
    accident = bool(traffic_report.get("accident_status", traffic_report.get("accident", False)))
    emergency_vehicle = bool(traffic_report.get("emergency_vehicle_status", traffic_report.get("emergency_vehicle", False)))
    emergency_type = (traffic_report.get("emergency_type") or "AMBULANCE").upper() if emergency_vehicle else "NONE"
    
    # Check density across both 'traffic_density' and 'density' keys
    density_raw = traffic_report.get("traffic_density", traffic_report.get("density", "MEDIUM"))
    density = str(density_raw).upper()

    # Emergency Classification Logic
    if emergency_type == "AMBULANCE" or (emergency_vehicle and "AMBULANCE" in emergency_type):
        event_type = "MEDICAL EMERGENCY"
        severity = "CRITICAL"
        priority_level = "MEDICAL EMERGENCY"
    elif emergency_type == "FIRE TRUCK" or (emergency_vehicle and "FIRE" in emergency_type):
        event_type = "FIRE EMERGENCY"
        severity = "CRITICAL"
        priority_level = "FIRE EMERGENCY"
    elif emergency_type == "POLICE VEHICLE" or (emergency_vehicle and "POLICE" in emergency_type):
        event_type = "POLICE EMERGENCY"
        severity = "HIGH"
        priority_level = "POLICE EMERGENCY"
    elif accident and (density in ["HIGH", "CRITICAL"] or congestion_info.get("congestion_score", 0) >= 70):
        event_type = "CRITICAL ACCIDENT"
        severity = "CRITICAL"
        priority_level = "CRITICAL ACCIDENT"
    elif accident:
        event_type = "ACCIDENT"
        severity = "HIGH"
        priority_level = "ACCIDENT"
    elif density in ["HIGH", "CRITICAL"] or congestion_info.get("congestion_score", 0) >= 60:
        event_type = "HIGH TRAFFIC"
        severity = "MEDIUM"
        priority_level = "HIGH TRAFFIC"
    else:
        event_type = "NORMAL"
        severity = "LOW"
        priority_level = "NORMAL"

    has_emergency = (event_type != "NORMAL" and event_type != "HIGH TRAFFIC")
    green_corridor_active = has_emergency and (emergency_vehicle or severity == "CRITICAL")
    alternates = congestion_info.get("recommended_alternate_roads", ["Outer Ring Road", "Bypass Expressway"])

    corridor_route = [road] + (alternates[:1] if alternates else ["Outer Ring Road"])
    
    if green_corridor_active:
        signal_override_status = f"ACTIVE: Zero-wait Green Corridor locked along {road} for {emergency_type if emergency_vehicle else 'Critical Emergency'}"
    elif accident:
        signal_override_status = f"ACTIVE: Accident Response Mode locked on {road}. Alternate route diversion recommended via {corridor_route[-1]}"
    else:
        signal_override_status = "INACTIVE: Standard adaptive signal timing schedule active"

    logger.info(f"[AGENT] Emergency classification for {road}: Event={event_type}, Severity={severity}, GreenCorridor={green_corridor_active}")

    return {
        "emergency_detected": has_emergency,
        "event_type": event_type,
        "severity": severity,
        "priority_level": priority_level,
        "vehicle_type": emergency_type if emergency_vehicle else ("INCIDENT UNIT" if accident else "NONE"),
        "green_corridor_active": green_corridor_active,
        "corridor_route": corridor_route,
        "signal_override_status": signal_override_status,
        "affected_road": road,
        "location": {
            "latitude": traffic_report.get("location", {}).get("latitude", 13.0827),
            "longitude": traffic_report.get("location", {}).get("longitude", 80.2707)
        }
    }
