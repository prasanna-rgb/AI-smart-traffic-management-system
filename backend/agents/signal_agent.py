"""
Agent 4: Signal Optimization Agent
Optimizes traffic signal timing dynamically, increases green light durations, and reduces waiting time.
"""
import json
from typing import Dict, Any
try:
    from crewai import Agent
except Exception:
    Agent = None
from config.settings import get_llm


def create_signal_agent() -> Agent:
    """Factory to create CrewAI Signal Optimization Agent."""
    llm = get_llm()
    return Agent(
        role="Signal Optimization Agent",
        goal="Dynamically optimize signal timing, extend green light phases, reduce intersection queue wait times, and clear congestion.",
        backstory=(
            "You are a Cyber-Physical Traffic Controller AI. You adjust micro-timing parameters of smart signal nodes. "
            "When congestion increases or an emergency corridor is activated, you dynamically adjust green splits and cycle lengths "
            "to maximize throughput and minimize vehicle delay."
        ),
        verbose=True,
        memory=True,
        llm=llm
    )


def process_signal_rule_based(traffic_report: Dict[str, Any], congestion_info: Dict[str, Any], emergency_info: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic fallback logic for Signal Optimization Agent."""
    road = traffic_report.get("road", "Main Road")
    congestion_score = congestion_info.get("congestion_score", 40.0)
    green_corridor = emergency_info.get("green_corridor_active", False)

    base_green_sec = 30

    if green_corridor:
        signal_mode = "Green-Corridor-Override"
        recommended_green = 90
        dynamic_increase = 60
        wait_reduction_pct = 85.0
    elif congestion_score >= 75.0:
        signal_mode = "Dynamic-High-Density"
        recommended_green = 65
        dynamic_increase = 35
        wait_reduction_pct = 42.5
    elif congestion_score >= 50.0:
        signal_mode = "Dynamic-Moderate-Density"
        recommended_green = 45
        dynamic_increase = 15
        wait_reduction_pct = 25.0
    else:
        signal_mode = "Standard-Balanced"
        recommended_green = 30
        dynamic_increase = 0
        wait_reduction_pct = 10.0

    return {
        "junction": f"{road} Intersecting Junction",
        "current_green_time_sec": base_green_sec,
        "recommended_green_time_sec": recommended_green,
        "dynamic_increase_sec": dynamic_increase,
        "estimated_wait_time_reduction_pct": wait_reduction_pct,
        "signal_mode": signal_mode
    }
