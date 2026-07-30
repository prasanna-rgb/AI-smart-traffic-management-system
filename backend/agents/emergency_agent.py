"""
Emergency Agent: Detects emergency vehicles and coordinates multi-intersection green corridors.
"""
from typing import Dict, Any, List
from config.settings import get_llm

try:
    from crewai import Agent
    CREWAI_AVAILABLE = True
except Exception:
    CREWAI_AVAILABLE = False
    Agent = None

def create_emergency_agent():
    if not CREWAI_AVAILABLE:
        return None
    llm = get_llm()
    return Agent(
        role="Emergency Response & First Responder Transport Coordinator",
        goal="Detect emergency vehicles (ambulances, fire engines, police), evaluate priority level (1-10), and clear green corridors across interconnected intersections.",
        backstory="""You are a Command Center First-Responder Coordinator. You ensure zero-delay travel paths for emergency vehicles by overriding normal traffic cycles and clearing multi-intersection paths.""",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

def process_emergency_rule_based(vision_output: Dict[str, Any], analysis_output: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic rule engine for Emergency Agent preemption."""
    breakdown = vision_output.get("fleet_breakdown", {})
    ambulance_count = breakdown.get("ambulance", 0)
    has_emergency = vision_output.get("emergency_vehicle_detected", False) or ambulance_count > 0

    intersection_code = vision_output.get("intersection_code", "INT-01")

    corridor_networks = {
        "INT-01": ["INT-01", "INT-02", "INT-03"],
        "INT-02": ["INT-02", "INT-03", "INT-04"],
        "INT-03": ["INT-03", "INT-01"],
        "INT-04": ["INT-04", "INT-02"]
    }

    green_corridor_route = corridor_networks.get(intersection_code, [intersection_code])

    if has_emergency:
        priority = 10 if ambulance_count > 0 else 8
        status = "ACTIVE_PREEMPTION"
        action = f"🚨 GREEN CORRIDOR ACTIVATED along route {green_corridor_route}. Priority {priority} override applied to clear emergency vehicle."
    else:
        priority = 0
        status = "STANDBY"
        action = "No emergency vehicle detected. Normal signal control operating."

    return {
        "intersection_code": intersection_code,
        "emergency_detected": has_emergency,
        "vehicle_type": "AMBULANCE" if has_emergency else "NONE",
        "priority_level": priority,
        "green_corridor_active": has_emergency,
        "route_corridor": green_corridor_route,
        "status": status,
        "action_taken": action
    }
