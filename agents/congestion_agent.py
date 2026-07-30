"""
Agent 2: Congestion Prediction Agent
Evaluates Traffic Reports, calculates congestion scores (0-100), predicts traffic trends, and recommends bypass routes.
"""
import json
from typing import Dict, Any
try:
    from crewai import Agent
except Exception:
    Agent = None
from config.settings import get_llm

ALTERNATE_ROUTES = {
    "Main Road": ["Outer Ring Road", "Park Bypass Way"],
    "Broadway Ave": ["5th Avenue Expressway", "Metro Underpass Drive"],
    "Express Highway": ["Service Lane North", "Old City Arterial"],
    "Downtown Ring": ["Commercial Beltway", "Riverfront Road"],
    "Harbor View Park": ["Coastal Boulevard", "Harbor Flyover"]
}


def create_congestion_agent() -> Agent:
    """Factory to create CrewAI Congestion Prediction Agent."""
    llm = get_llm()
    return Agent(
        role="Congestion Prediction Agent",
        goal="Predict traffic congestion severity, calculate congestion scores (0-100), and recommend alternative bypass routes.",
        backstory=(
            "You are an advanced Predictive Transport Analytics AI. You analyze real-time density, "
            "speed reductions, and weather hazards to estimate congestion scores, project 30-minute traffic trends, "
            "and suggest optimal detour routes to prevent gridlock."
        ),
        verbose=True,
        memory=True,
        llm=llm
    )


def process_congestion_rule_based(traffic_report: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic fallback logic for Congestion Prediction Agent."""
    road = traffic_report.get("road", "Main Road")
    vehicles = traffic_report.get("vehicles", 50)
    speed = traffic_report.get("average_speed", 40.0)
    density = traffic_report.get("density", "Medium")
    accident = traffic_report.get("accident", False)
    weather = traffic_report.get("weather", "Clear")

    # Base Score Calculation
    base_score = min(100.0, (vehicles / 120.0) * 60.0 + (max(0, 60.0 - speed) / 60.0) * 40.0)
    
    if accident:
        base_score = min(100.0, base_score + 25.0)
    if weather in ["Rain", "Fog"]:
        base_score = min(100.0, base_score + 10.0)
    elif weather == "Storm":
        base_score = min(100.0, base_score + 20.0)

    score = round(base_score, 1)

    # Risk level classification
    if score >= 80.0:
        risk_level = "Severe"
        predicted_trend = "Rapidly Increasing"
        est_delay = round(15.0 + (score - 80) * 0.5, 1)
    elif score >= 60.0:
        risk_level = "High"
        predicted_trend = "Increasing"
        est_delay = round(8.0 + (score - 60) * 0.35, 1)
    elif score >= 35.0:
        risk_level = "Moderate"
        predicted_trend = "Stable"
        est_delay = round(3.0 + (score - 35) * 0.2, 1)
    else:
        risk_level = "Low"
        predicted_trend = "Decreasing"
        est_delay = 1.0

    alternates = ALTERNATE_ROUTES.get(road, ["City Bypass Route A", "Secondary Service Road"])

    return {
        "road": road,
        "congestion_score": score,
        "risk_level": risk_level,
        "predicted_trend": predicted_trend,
        "estimated_delay_minutes": est_delay,
        "recommended_alternate_roads": alternates
    }
