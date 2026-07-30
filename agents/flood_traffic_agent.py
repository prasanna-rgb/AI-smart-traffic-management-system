"""
Flood & Waterlogging Traffic Agent.
Detects, predicts, and monitors road flooding and waterlogging risks before severe traffic congestion occurs.
"""

import logging
from typing import Dict, Any, Optional

try:
    from crewai import Agent
except Exception:
    Agent = None

from config.settings import get_llm
from tools.flood_data_tools import evaluate_flood_and_waterlogging_tool, FloodRiskCalculator


logger = logging.getLogger("smart_traffic_ai.agents.flood")


def create_flood_traffic_agent() -> Optional[Agent]:
    """
    Creates and configures the Flood & Waterlogging Traffic Intelligence Agent.
    """
    if Agent is None:
        logger.warning("CrewAI package not available. Returning None for Flood Traffic Agent.")
        return None

    llm = get_llm()
    
    return Agent(
        role="Flood & Waterlogging Traffic Intelligence Specialist",
        goal="Predict road flooding and waterlogging risks using rainfall, elevation, historical flood frequency, and traffic telemetry, recommending preventive signal and routing actions.",
        backstory=(
            "You are an expert AI climate-resilient traffic specialist. You integrate real-time rainfall data, "
            "road elevation profiles, drainage capacity, historical flood frequency, and live vehicle speeds "
            "to predict waterlogging hours before it occurs, ensuring proactive rerouting and early citizen alerts."
        ),
        tools=[evaluate_flood_and_waterlogging_tool],
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def process_flood_traffic_rule_based(telemetry: Dict[str, Any], weather_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Rule-based execution engine for Flood & Waterlogging Traffic Intelligence.
    """
    road_name = telemetry.get("road_name", telemetry.get("road", "Main Road"))
    
    # Extract rainfall intensity from weather info or telemetry
    weather_str = str(telemetry.get("weather", "Clear"))
    rainfall = float(telemetry.get("rainfall_mm_per_hour", 0.0))
    
    if rainfall == 0.0:
        if "heavy rain" in weather_str.lower() or "storm" in weather_str.lower():
            rainfall = 65.0
        elif "rain" in weather_str.lower() or "shower" in weather_str.lower():
            rainfall = 25.0
        elif "drizzle" in weather_str.lower():
            rainfall = 8.0

    speed = float(telemetry.get("average_speed", 30.0))
    density = str(telemetry.get("traffic_density", "MEDIUM"))
    water_sensor = telemetry.get("sensor_water_level_cm")

    risk_res = FloodRiskCalculator.calculate_risk(
        road_name=road_name,
        rainfall_mm_per_hour=rainfall,
        weather_condition=weather_str,
        vehicle_speed=speed,
        traffic_density=density,
        sensor_water_level_cm=water_sensor
    )

    logger.info(f"Flood Risk evaluated for {road_name}: Score {risk_res['flood_risk_score']}/100 ({risk_res['risk_level']})")
    return risk_res
