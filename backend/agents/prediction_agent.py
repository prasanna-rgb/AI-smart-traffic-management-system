"""
Prediction Agent: Forecasts short-term congestion trends (5, 10, 15, 30 min horizons).
"""
import math
import random
from typing import Dict, Any
from config.settings import get_llm

try:
    from crewai import Agent
    CREWAI_AVAILABLE = True
except Exception:
    CREWAI_AVAILABLE = False
    Agent = None

def create_prediction_agent():
    if not CREWAI_AVAILABLE:
        return None
    llm = get_llm()
    return Agent(
        role="Predictive Traffic Data Scientist & Time-Series Specialist",
        goal="Forecast short-term congestion index trends (+5, +10, +15, +30 minutes) using current inflow rate, historical demand, and spatial dynamics.",
        backstory="""You are an expert AI Time-Series Forecaster. You utilize autoregressive trend modeling and inflow/outflow balance to predict future traffic surges before bottlenecks form.""",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

def process_prediction_rule_based(vision_output: Dict[str, Any], analysis_output: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic rule engine for Prediction Agent forecasting."""
    current_density = vision_output.get("density_pct", 40.0)
    los = analysis_output.get("level_of_service", "C")

    trend_factor = 1.05 if current_density > 60 else (0.95 if current_density < 30 else 1.0)

    score_5m = min(100.0, max(0.0, round(current_density * math.pow(trend_factor, 0.5), 1)))
    score_10m = min(100.0, max(0.0, round(current_density * math.pow(trend_factor, 1.0), 1)))
    score_15m = min(100.0, max(0.0, round(current_density * math.pow(trend_factor, 1.5), 1)))
    score_30m = min(100.0, max(0.0, round(current_density * math.pow(trend_factor, 2.0), 1)))

    if score_15m > 75.0:
        predicted_los = "E/F"
        trend_summary = "CRITICAL CONGESTION RISKS IN NEXT 15 MIN. Immediate signal split extension recommended."
    elif score_15m > 55.0:
        predicted_los = "D"
        trend_summary = "MODERATE INFLOW BUILDUP EXPECTED. Upward trend expected over 15-30 minute window."
    else:
        predicted_los = "A/B"
        trend_summary = "STABLE TRAFFIC FLOW. No major bottleneck surge projected in short-term horizon."

    return {
        "intersection_code": vision_output.get("intersection_code", "INT-01"),
        "current_congestion_score": current_density,
        "forecast": {
            "5_min": score_5m,
            "10_min": score_10m,
            "15_min": score_15m,
            "30_min": score_30m
        },
        "predicted_los_15m": predicted_los,
        "trend_summary": trend_summary
    }
