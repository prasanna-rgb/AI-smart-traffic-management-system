"""
Agent 5: Citizen Communication Agent
Generates actionable citizen traffic alerts, road closure notices, accident warnings, and alternate route advisories.
"""
import json
import uuid
from datetime import datetime
from typing import Dict, Any
try:
    from crewai import Agent
except Exception:
    Agent = None
from config.settings import get_llm


def create_citizen_agent() -> Agent:
    """Factory to create CrewAI Citizen Communication Agent."""
    llm = get_llm()
    return Agent(
        role="Citizen Communication Agent",
        goal="Generate clear, timely public traffic warnings, accident broadcasts, emergency lane clearing alerts, and detour advice.",
        backstory=(
            "You are an Urban Mobility Public Information AI. Your duty is to communicate critical traffic updates to commuters "
            "via mobile applications, radio feeds, and digital highway VMS (Variable Message Signs), providing actionable detour recommendations."
        ),
        verbose=True,
        memory=True,
        llm=llm
    )


def process_citizen_rule_based(traffic_report: Dict[str, Any], congestion_info: Dict[str, Any], emergency_info: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic fallback logic for Citizen Communication Agent."""
    road = traffic_report.get("road", "Main Road")
    accident = traffic_report.get("accident", False)
    green_corridor = emergency_info.get("green_corridor_active", False)
    emergency_type = emergency_info.get("vehicle_type", "Emergency Vehicle")
    alternates = congestion_info.get("recommended_alternate_roads", ["Bypass Route"])

    alert_id = f"ALT-{uuid.uuid4().hex[:6].upper()}"
    timestamp = datetime.utcnow().isoformat()

    if green_corridor:
        title = f"🚨 EMERGENCY CORRIDOR ACTIVE - {road.upper()}"
        severity = "EMERGENCY"
        message = f"An active {emergency_type} Green Corridor is operational along {road}. All non-emergency vehicles must yield right-of-way immediately."
        alternate_route = alternates[0] if alternates else None
    elif accident:
        title = f"⚠️ ACCIDENT ALERT ON {road.upper()}"
        severity = "CRITICAL"
        message = f"Accident reported on {road}. High delay expected. Please divert to alternate routes."
        alternate_route = alternates[0] if alternates else None
    elif congestion_info.get("congestion_score", 0) > 70:
        title = f"🚗 HEAVY CONGESTION WARNING - {road.upper()}"
        severity = "WARNING"
        message = f"Severe traffic density detected on {road}. Estimated delay: {congestion_info.get('estimated_delay_minutes', 15)} mins."
        alternate_route = alternates[0] if alternates else None
    else:
        title = f"ℹ️ TRAFFIC FLOW NORMAL - {road.upper()}"
        severity = "INFO"
        message = f"Traffic on {road} is flowing smoothly with average speed of {traffic_report.get('average_speed', 45)} km/h."
        alternate_route = None

    return {
        "alert_id": alert_id,
        "timestamp": timestamp,
        "title": title,
        "severity": severity,
        "message": message,
        "affected_road": road,
        "alternate_route": alternate_route,
        "broadcast_channels": ["Mobile App", "Variable Message Signs", "Radio FM", "Smart City Portal"]
    }
