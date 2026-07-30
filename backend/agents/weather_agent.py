"""
Agent 7: Smart Weather Adaptability Agent (Backend Package).
Analyzes weather conditions (Rain, Fog, Storm, Clear), adjusts safe speed limits, extends green light durations, and issues driver weather hazard warnings.
"""
from typing import Dict, Any

try:
    from crewai import Agent
except Exception:
    Agent = None

from config.settings import get_llm


def create_weather_agent() -> Agent:
    """Factory to create CrewAI Smart Weather Adaptability Agent."""
    if Agent is None:
        return None
    llm = get_llm()
    return Agent(
        role="Smart Weather Adaptability Agent",
        goal="Analyze meteorological telemetry, calculate wet-road friction reduction, adjust safe advisory speed limits, extend junction green signals, and issue weather hazard warnings.",
        backstory=(
            "You are an Advanced Meteorological Transportation AI. You continuously monitor rain, fog, and storm telemetry. "
            "Because wet roads reduce tire traction and increase stopping distances, you automatically reduce recommended speed limits, "
            "extend green signal phases to prevent sudden braking hydroplaning, and alert drivers to adverse conditions."
        ),
        verbose=True,
        memory=True,
        llm=llm
    )


def process_weather_rule_based(traffic_report: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic fallback logic for Smart Weather Agent."""
    road = traffic_report.get("road_name", traffic_report.get("road", "Main Road"))
    weather = str(traffic_report.get("weather", "Clear")).title()
    current_speed = traffic_report.get("average_speed", 45.0)

    if weather in ["Rain", "Heavy Rain"]:
        rec_speed_limit = 40.0
        green_extension_sec = 15
        visibility_m = 250
        friction_idx = 0.55
        warning_msg = f"[RAIN ADVISORY] Reduced speed limit to {rec_speed_limit} km/h on {road}. Extended green signal +15s to prevent wet braking skids."
    elif weather in ["Storm", "Thunderstorm"]:
        rec_speed_limit = 30.0
        green_extension_sec = 25
        visibility_m = 100
        friction_idx = 0.38
        warning_msg = f"[SEVERE STORM ALERT] Speed limit reduced to {rec_speed_limit} km/h on {road}. High hydroplaning risk! Maintain 50m follow distance."
    elif weather == "Fog":
        rec_speed_limit = 30.0
        green_extension_sec = 20
        visibility_m = 50
        friction_idx = 0.60
        warning_msg = f"[DENSE FOG WARNING] Visibility < 50m on {road}. Speed limit capped at {rec_speed_limit} km/h. Headlights & hazard lights mandatory."
    else:  # Clear / Dry
        rec_speed_limit = 60.0
        green_extension_sec = 0
        visibility_m = 1000
        friction_idx = 0.85
        warning_msg = f"[CLEAR WEATHER] Standard speed limit of {rec_speed_limit} km/h operational on {road}."

    speed_reduction_pct = round(max(0.0, ((60.0 - rec_speed_limit) / 60.0) * 100.0), 1)

    return {
        "road": road,
        "weather_condition": weather,
        "recommended_speed_limit_kmh": rec_speed_limit,
        "speed_reduction_pct": speed_reduction_pct,
        "weather_green_extension_sec": green_extension_sec,
        "visibility_meters": visibility_m,
        "road_friction_index": friction_idx,
        "driver_weather_warning": warning_msg
    }
