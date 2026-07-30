"""
Specialized Agent: Emergency Resource Allocation Agent (Backend Package).
"""

from typing import Dict, Any
try:
    from crewai import Agent
except Exception:
    Agent = None

from config.settings import get_llm
from backend.tools.emergency_resource_tools import ResourceAllocatorEngine, allocate_emergency_resources_tool


def create_emergency_resource_agent() -> Agent:
    """Factory to create CrewAI Emergency Resource Allocation Agent."""
    llm = get_llm()
    if Agent is None:
        return None
    return Agent(
        role="Emergency Resource Allocation Specialist",
        goal="Select optimal ambulance, hospital, and emergency route using real-time traffic and medical resource information.",
        backstory=(
            "You are an intelligent emergency logistics specialist that coordinates ambulances, hospitals, routes, "
            "traffic conditions, and emergency resources to minimize response time and improve emergency-care outcomes. "
            "You compare all available ambulances and regional hospitals, scoring them on travel time, traffic, medical capability, "
            "ICU availability, and trauma center capabilities to make the best emergency resource allocation decision."
        ),
        tools=[allocate_emergency_resources_tool],
        verbose=True,
        memory=True,
        llm=llm
    )


def process_emergency_resource_allocation_rule_based(telemetry: Dict[str, Any], emergency_info: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Deterministic rule-based execution engine for Emergency Resource Allocation Agent.
    """
    em = emergency_info or {}
    accident_id = telemetry.get("accident_id", f"ACC-{telemetry.get('road', 'INT101')[:3].upper()}")
    road_name = telemetry.get("road_name", telemetry.get("road", "Main Road"))
    severity = em.get("severity", "CRITICAL" if telemetry.get("accident") else "NORMAL")
    traffic = telemetry.get("density", "HIGH")

    acc_payload = {
        "accident_id": accident_id,
        "road_name": road_name,
        "severity": severity,
        "latitude": float(telemetry.get("latitude", 13.0827)),
        "longitude": float(telemetry.get("longitude", 80.2707)),
        "traffic_density": traffic,
        "estimated_injuries": 3 if severity in ["CRITICAL", "HIGH"] else 1,
        "fire_detected": False,
        "airbag_deployed": True if severity == "CRITICAL" else False
    }

    return ResourceAllocatorEngine.allocate_resources(acc_payload)
