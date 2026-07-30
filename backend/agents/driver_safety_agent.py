"""
Specialized Agent: Driver Behavior & Safety Analytics Agent (Backend Package).
Continuously analyzes driver and vehicle telemetry to detect 8 violation types,
computes Driver Safety Score (0-100), risk levels, risk predictions, location intelligence, and safety alerts.
"""

from typing import Dict, Any
try:
    from crewai import Agent
    CREWAI_AVAILABLE = True
except Exception:
    CREWAI_AVAILABLE = False
    Agent = None

from config.settings import get_llm
from tools.driver_behavior_tools import DriverBehaviorTools


def create_driver_safety_agent() -> Agent:
    """Factory to create CrewAI Driver Behavior & Safety Analytics Agent."""
    if not CREWAI_AVAILABLE or Agent is None:
        return None
    llm = get_llm()
    return Agent(
        role="Driver Behavior & Safety Analytics Agent",
        goal="Continuously analyze driver and vehicle telemetry, detect hazardous driving violations, compute Driver Safety Score, predict risk, and generate alerts.",
        backstory=(
            "You are the Chief Road Safety & Driver Behavior Analytics AI at the Smart City Command Center. "
            "Your job is to analyze real-time and simulated vehicle telemetry for sudden braking, wrong-way driving, overspeeding, "
            "illegal U-turns, lane drift violations, and dangerous driving patterns. "
            "You evaluate Driver Safety Scores (0-100), classify Risk Levels (LOW, MEDIUM, HIGH, CRITICAL), "
            "predict future driver risk, log violation locations for hotspot analysis, and generate safety alerts."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm
    )


def process_driver_safety_rule_based(telemetry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic rule-based execution engine for Driver Behavior & Safety Agent.
    
    Args:
        telemetry: Raw or formatted traffic/vehicle telemetry.
        
    Returns:
        Structured driver safety report dictionary.
    """
    return DriverBehaviorTools.evaluate_telemetry(telemetry)
