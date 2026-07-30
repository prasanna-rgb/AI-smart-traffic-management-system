"""
Agent 3: Emergency Vehicle Agent
Detects emergency vehicles (Ambulance, Fire Truck, Police), plans Green Corridors, and overrides signal cycles.
"""
import json
from typing import Dict, Any
try:
    from crewai import Agent
except Exception:
    Agent = None
from config.settings import get_llm


def create_emergency_agent() -> Agent:
    """Factory to create CrewAI Emergency Vehicle Agent."""
    llm = get_llm()
    return Agent(
        role="Emergency Vehicle Agent",
        goal="Detect ambulances, fire trucks, and police vehicles, create immediate Green Corridors, and notify signal controllers.",
        backstory=(
            "You are a critical Priority Dispatch AI specializing in emergency life-safety routing. "
            "When emergency vehicles are detected, you preempt standard traffic light cycles, generate a zero-wait Green Corridor, "
            "and alert signal controllers to clear the emergency vehicle's path."
        ),
        verbose=True,
        memory=True,
        llm=llm
    )


def process_emergency_rule_based(traffic_report: Dict[str, Any], congestion_info: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic fallback logic for Emergency Vehicle Agent."""
    has_emergency = traffic_report.get("emergency_vehicle", False)
    emergency_type = traffic_report.get("emergency_type", "Ambulance") if has_emergency else None
    road = traffic_report.get("road", "Main Road")
    alternates = congestion_info.get("recommended_alternate_roads", ["Express Corridor"])

    if has_emergency:
        priority_level = "EMERGENCY_PREEMPTION"
        corridor_route = [road] + alternates[:1]
        signal_override_status = f"ACTIVE: All green signals locked along {road} for incoming {emergency_type}"
        green_corridor_active = True
    else:
        priority_level = "Normal"
        corridor_route = []
        signal_override_status = "INACTIVE: Standard signal schedule running"
        green_corridor_active = False

    return {
        "emergency_detected": has_emergency,
        "vehicle_type": emergency_type,
        "green_corridor_active": green_corridor_active,
        "corridor_route": corridor_route,
        "signal_override_status": signal_override_status,
        "priority_level": priority_level
    }
