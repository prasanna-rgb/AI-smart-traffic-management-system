"""
Traffic Analysis Agent: Calculates Level of Service (LOS A-F), queue lengths, occupancy, and bottlenecks.
"""
from typing import Dict, Any
from config.settings import get_llm

try:
    from crewai import Agent
    CREWAI_AVAILABLE = True
except Exception:
    CREWAI_AVAILABLE = False
    Agent = None

def create_traffic_analysis_agent():
    if not CREWAI_AVAILABLE:
        return None
    llm = get_llm()
    return Agent(
        role="Senior Traffic Flow & Capacity Planning Analyst",
        goal="Evaluate intersection capacity, calculate Level of Service (LOS grade A to F), estimate vehicle queue lengths, and diagnose bottleneck bottlenecks.",
        backstory="""You are an experienced Municipal Traffic Engineer specializing in Highway Capacity Manual (HCM) standards.
        You take vision telemetry metrics and compute rigorous flow rates, LOS scores, queue delays, and road occupancy percentages.""",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

def process_traffic_analysis_rule_based(vision_output: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic rule engine for Traffic Analysis Agent."""
    total_vehicles = vision_output.get("total_vehicles", 40)
    density_pct = vision_output.get("density_pct", 45.0)
    avg_speed = vision_output.get("average_speed_kmh", 35.0)

    if density_pct < 20 and avg_speed >= 50:
        los = "A"
        delay_sec = 8.5
    elif density_pct < 35 and avg_speed >= 40:
        los = "B"
        delay_sec = 14.2
    elif density_pct < 50 and avg_speed >= 30:
        los = "C"
        delay_sec = 22.0
    elif density_pct < 70 and avg_speed >= 20:
        los = "D"
        delay_sec = 38.5
    elif density_pct < 85 and avg_speed >= 12:
        los = "E"
        delay_sec = 56.0
    else:
        los = "F"
        delay_sec = 88.0

    queue_vehicles = max(0, int(total_vehicles * (density_pct / 100.0) * 0.7))
    queue_length_meters = queue_vehicles * 6.5

    is_bottleneck = los in ("E", "F") or density_pct > 75.0

    return {
        "intersection_code": vision_output.get("intersection_code", "INT-01"),
        "level_of_service": los,
        "average_control_delay_sec": round(delay_sec, 1),
        "estimated_queue_vehicles": queue_vehicles,
        "estimated_queue_length_m": round(queue_length_meters, 1),
        "occupancy_pct": density_pct,
        "is_bottleneck": is_bottleneck,
        "capacity_utilization": f"{min(100, int(density_pct * 1.15))}%",
        "analysis_summary": f"Intersection operating at LOS {los} with {queue_vehicles} vehicles queued ({round(queue_length_meters)}m length)."
    }
