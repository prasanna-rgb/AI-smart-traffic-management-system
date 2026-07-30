"""
Agent 5: Citizen Communication Agent
Generates actionable citizen traffic alerts, road closure notices, accident warnings,
WhatsApp alerts, and alternate route advisories.
"""
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, Any

try:
    from crewai import Agent
except Exception:
    Agent = None

from config.settings import get_llm

logger = logging.getLogger("smart_traffic_ai.agent.citizen")


def create_citizen_agent() -> Agent:
    """Factory to create CrewAI Citizen Communication Agent."""
    if Agent is None:
        return None
    llm = get_llm()
    return Agent(
        role="Citizen Communication Agent",
        goal="Generate clear, timely public traffic warnings, WhatsApp advisories, emergency lane clearing alerts, and detour advice.",
        backstory=(
            "You are an Urban Mobility Public Information AI. Your duty is to communicate critical traffic updates to commuters "
            "via mobile applications, WhatsApp notifications, radio feeds, and digital highway VMS signs, providing actionable detour recommendations."
        ),
        verbose=True,
        memory=True,
        llm=llm
    )


def process_citizen_rule_based(traffic_report: Dict[str, Any], congestion_info: Dict[str, Any], emergency_info: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic, safety-checked execution engine for Citizen Communication Agent."""
    road = traffic_report.get("road_name", traffic_report.get("road", "Main Road"))
    accident = bool(traffic_report.get("accident_status", traffic_report.get("accident", False)))
    green_corridor = bool(emergency_info.get("green_corridor_active", False))
    emergency_type = emergency_info.get("vehicle_type", "AMBULANCE")
    event_type = emergency_info.get("event_type", "ACCIDENT" if accident else "NORMAL")
    severity = emergency_info.get("severity", "CRITICAL" if (accident or green_corridor) else "INFO")
    alternates = congestion_info.get("recommended_alternate_roads", ["Outer Ring Road", "Bypass Expressway"])

    alert_id = f"ALT-{uuid.uuid4().hex[:6].upper()}"
    timestamp = datetime.utcnow().isoformat()
    alternate_route = alternates[0] if alternates else "Outer Ring Road"

    if green_corridor:
        title = f"🚨 EMERGENCY CORRIDOR ACTIVE - {road.upper()}"
        severity = "EMERGENCY"
        message = (
            f"🚨 EMERGENCY TRAFFIC ALERT\n\n"
            f"Active {emergency_type} Green Corridor operational along {road}.\n\n"
            f"Severity: {severity}\n"
            f"📍 Location: {road}\n"
            f"🚑 Emergency vehicle approaching.\n"
            f"🚦 Emergency Green Corridor activated.\n"
            f"⚠️ All non-emergency vehicles must yield right-of-way immediately.\n\n"
            f"🛣 Suggested alternate route: {alternate_route}\n\n"
            f"Drive safely."
        )
    elif accident:
        title = f"⚠️ ACCIDENT ALERT ON {road.upper()}"
        severity = "CRITICAL"
        message = (
            f"🚨 EMERGENCY TRAFFIC ALERT\n\n"
            f"Accident detected on {road}.\n\n"
            f"Severity: CRITICAL\n"
            f"📍 Location: {road}\n"
            f"🚑 Emergency response units dispatched.\n"
            f"⚠️ Heavy delay expected. Please avoid this route.\n\n"
            f"🛣 Suggested alternate route: {alternate_route}\n\n"
            f"Drive safely."
        )
    elif congestion_info.get("congestion_score", 0) > 70:
        title = f"🚗 HEAVY CONGESTION WARNING - {road.upper()}"
        severity = "WARNING"
        message = (
            f"⚠️ HEAVY TRAFFIC ADVISORY\n\n"
            f"Severe traffic density detected on {road}.\n"
            f"Estimated delay: {congestion_info.get('estimated_delay_minutes', 15)} mins.\n\n"
            f"🛣 Alternate route: {alternate_route}"
        )
    else:
        title = f"ℹ️ TRAFFIC FLOW NORMAL - {road.upper()}"
        severity = "INFO"
        message = f"Traffic on {road} is flowing smoothly with average speed of {traffic_report.get('average_speed', 45)} km/h."
        alternate_route = None

    logger.info(f"[AGENT] Citizen Communication alert generated: Title={title}, Severity={severity}")

    return {
        "alert_id": alert_id,
        "timestamp": timestamp,
        "title": title,
        "severity": severity,
        "message": message,
        "affected_road": road,
        "alternate_route": alternate_route,
        "broadcast_channels": ["WhatsApp Notification", "Mobile App", "Variable Message Signs", "Radio FM"]
    }
