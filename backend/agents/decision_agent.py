"""
Decision Agent: LLM reasoning over all agent outputs, signal timing split optimization, and Explainable AI (XAI) natural language decision generation.
"""
import json
import logging
from typing import Dict, Any
from config.settings import get_llm

logger = logging.getLogger("smart_traffic_ai.agents.decision")

try:
    from crewai import Agent
    CREWAI_AVAILABLE = True
except Exception:
    CREWAI_AVAILABLE = False
    Agent = None

def create_decision_agent():
    if not CREWAI_AVAILABLE:
        return None
    llm = get_llm()
    return Agent(
        role="Chief AI Traffic Director & Explainable Reasoning Engine",
        goal="Synthesize telemetry from Vision, Analysis, Prediction, Pollution, and Emergency agents to optimize signal phase splits and generate natural language decision explanations.",
        backstory="""You are the central AI Decision Controller for the Smart Traffic Network. You analyze safety, emergency preemption, emissions impact, and capacity to adjust signal timers dynamically while generating clear XAI audit logs.""",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

def process_decision_rule_based(
    vision_data: Dict[str, Any],
    analysis_data: Dict[str, Any],
    prediction_data: Dict[str, Any],
    pollution_data: Dict[str, Any],
    emergency_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Deterministic reasoning engine for Decision Agent when LLM key is absent or offline."""
    code = vision_data.get("intersection_code", "INT-01")
    density = vision_data.get("density_pct", 40.0)
    total_veh = vision_data.get("total_vehicles", 35)
    los = analysis_data.get("level_of_service", "C")
    pred_15m = prediction_data.get("forecast", {}).get("15_min", 45.0)
    co2 = pollution_data.get("co2_kg_hr", 25.0)
    has_emergency = emergency_data.get("green_corridor_active", False)

    if has_emergency:
        signal_mode = "EMERGENCY_CORRIDOR"
        ns_green = 75
        ew_green = 15
        active_phase = "NORTH_SOUTH_GREEN"
        reasoning = (
            f"🚨 EMERGENCY PREEMPTION TRIGGERED for {code}: Vision Agent detected an Ambulance. "
            f"Overriding standard cycle to grant priority GREEN corridor along North-South axis for 75 seconds. "
            f"East-West phase constrained to 15 seconds to flush queue."
        )
        action = f"Set {code} to EMERGENCY_CORRIDOR mode with NS=75s, EW=15s."
    elif density > 70 or pred_15m > 70:
        signal_mode = "AI_AUTO"
        ns_green = 55
        ew_green = 35
        active_phase = "NORTH_SOUTH_GREEN" if density > 50 else "EAST_WEST_GREEN"
        reasoning = (
            f"⚡ CONGESTION MITIGATION OPTIMIZATION for {code}: Traffic Analysis indicates LOS {los} with {total_veh} vehicles "
            f"and density at {density}%. Prediction Agent forecasts {pred_15m}% congestion in 15 mins. "
            f"Allocating extended 55s green duration to heavy inbound lane to alleviate queue buildup and lower CO2 idle emissions ({co2} kg/hr)."
        )
        action = f"Adjusted signal timing to NS={ns_green}s, EW={ew_green}s on AI_AUTO mode."
    else:
        signal_mode = "AI_AUTO"
        ns_green = 35
        ew_green = 30
        active_phase = "NORTH_SOUTH_GREEN"
        reasoning = (
            f"✅ BALANCED TRAFFIC OPTIMIZATION for {code}: Traffic operating smoothly at LOS {los} with density at {density}%. "
            f"Eco-Index is favorable with CO2 emissions at {co2} kg/hr. Maintaining standard balanced 35s/30s signal splits."
        )
        action = f"Maintained balanced cycle splits NS={ns_green}s, EW={ew_green}s."

    prompt_summary = f"Inputs: Vision({total_veh} veh, {density}%), Analysis(LOS {los}), Prediction(15m: {pred_15m}%), Pollution({co2}kg CO2/hr), Emergency({has_emergency})"

    return {
        "intersection_code": code,
        "agent_name": "Decision Agent",
        "decision_type": "SIGNAL_OPTIMIZATION",
        "signal_mode": signal_mode,
        "active_phase": active_phase,
        "recommended_splits": {
            "north_south_green_sec": ns_green,
            "east_west_green_sec": ew_green
        },
        "natural_language_reasoning": reasoning,
        "llm_prompt_summary": prompt_summary,
        "action_taken": action
    }
