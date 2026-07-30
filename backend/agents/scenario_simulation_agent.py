"""
New Agent: Traffic Scenario Simulation & Decision Agent (Backend Package).
Proactively evaluates possible traffic management actions before execution, 
predicts multi-metric outcomes, calculates decision scores, and recommends optimal strategies to down-stream agents.
"""
import logging
from typing import Dict, Any, Optional

try:
    from crewai import Agent
except Exception:
    Agent = None

from config.settings import get_llm
from backend.tools.scenario_simulation_tools import ScenarioSimulator, simulate_traffic_scenarios_tool

logger = logging.getLogger("smart_traffic_ai.agent.scenario_simulation")


def create_scenario_simulation_agent() -> Agent:
    """Factory to create CrewAI Traffic Scenario Simulation & Decision Agent."""
    if Agent is None:
        return None
    llm = get_llm()
    return Agent(
        role="Traffic Scenario Simulation & Decision Specialist",
        goal="Evaluate possible traffic-management actions, simulate multi-metric outcomes, compare candidate strategies, and recommend the safest and most efficient strategy.",
        backstory=(
            "You are an advanced AI decision-support specialist functioning as the Decision Intelligence Layer. "
            "Before traffic signals change or traffic is rerouted, you ask 'What will happen if I take this action?', "
            "simulate candidate scenarios (signal extension, emergency corridor, alternate route diversion), "
            "calculate decision scores across congestion, emergency response time, travel delay, and carbon emissions, "
            "and recommend the winning strategy to other agents."
        ),
        verbose=True,
        memory=True,
        tools=[simulate_traffic_scenarios_tool],
        llm=llm
    )


def process_scenario_simulation_rule_based(traffic_data: Dict[str, Any], congestion_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Deterministic, safety-checked execution engine for Traffic Scenario Simulation & Decision Agent."""
    logger.info("[SCENARIO] Current traffic received for decision simulation")
    logger.info("[SCENARIO] Generating possible strategies")

    sim_input = dict(traffic_data)
    if congestion_info:
        sim_input["congestion_score"] = congestion_info.get("congestion_score", sim_input.get("congestion_level", 40))
        sim_input["recommended_alternate_roads"] = congestion_info.get("recommended_alternate_roads", [])

    logger.info("[SCENARIO] Scenario A simulation started: Baseline Current Timing")
    logger.info("[SCENARIO] Scenario B simulation started: Extended Green Signal Phase")
    logger.info("[SCENARIO] Scenario C simulation started: Emergency Green Corridor")
    logger.info("[SCENARIO] Scenario D simulation started: Combined Corridor + Alternate Reroute")
    logger.info("[SCENARIO] Calculating decision scores")

    simulation_result = ScenarioSimulator.simulate_scenarios(sim_input)

    logger.info(f"[SCENARIO] Best scenario selected: {simulation_result.get('winning_scenario_id')} - Score={simulation_result.get('decision_score')}")
    logger.info(f"[SCENARIO] Recommendation sent to Signal Agent & Emergency Agent")

    return simulation_result
