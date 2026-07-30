"""
Flood & Waterlogging Data Tools and Risk Calculation Engine.
Calculates road-level Flood Risk Scores (0-100), predicts early waterlogging probability,
classifies road safety levels, and recommends alternate detour routes.
"""

import json
import logging
from typing import Dict, Any, List, Optional
try:
    from crewai.tools import tool
except Exception:
    def tool(name_or_func=None):
        def decorator(func):
            return func
        return decorator(name_or_func) if callable(name_or_func) else decorator


logger = logging.getLogger("smart_traffic_ai.tools.flood")


# Static Road Elevation, Drainage & Historical Flood Registry
ROAD_FLOOD_REGISTRY = {
    "Main Road": {
        "road_id": "R101",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "elevation_meters": 5.2,
        "historical_flood_risk": "HIGH",
        "historical_flood_score": 85,
        "drainage_condition": "POOR",
        "drainage_score": 80,
        "alternate_route": "Ring Road Bypass (Elevated)"
    },
    "Broadway Ave": {
        "road_id": "R102",
        "latitude": 13.0850,
        "longitude": 80.2750,
        "elevation_meters": 8.1,
        "historical_flood_risk": "MEDIUM",
        "historical_flood_score": 45,
        "drainage_condition": "FAIR",
        "drainage_score": 50,
        "alternate_route": "Grand Trunk Road"
    },
    "Express Highway": {
        "road_id": "R103",
        "latitude": 13.0900,
        "longitude": 80.2800,
        "elevation_meters": 14.5,
        "historical_flood_risk": "LOW",
        "historical_flood_score": 10,
        "drainage_condition": "EXCELLENT",
        "drainage_score": 10,
        "alternate_route": "Service Lane"
    },
    "Harbor View Park": {
        "road_id": "R104",
        "latitude": 13.0950,
        "longitude": 80.2850,
        "elevation_meters": 3.8,
        "historical_flood_risk": "CRITICAL",
        "historical_flood_score": 95,
        "drainage_condition": "BLOCKED",
        "drainage_score": 90,
        "alternate_route": "Coastal Flyover"
    }
}


class FloodRiskCalculator:
    """Multi-Attribute Configurable Flood Risk Calculator."""

    WEIGHTS = {
        "rainfall": 0.30,
        "history": 0.20,
        "water_level": 0.20,
        "elevation": 0.15,
        "traffic": 0.10,
        "drainage": 0.05
    }

    @classmethod
    def calculate_risk(
        cls,
        road_name: str,
        rainfall_mm_per_hour: float,
        weather_condition: str = "Rain",
        vehicle_speed: float = 30.0,
        traffic_density: str = "MEDIUM",
        sensor_water_level_cm: Optional[float] = None,
        override_elevation: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Compute 0-100 Flood Risk Score using multi-factor weighted formula:
        Score = 30% Rainfall + 20% History + 20% WaterLevel + 15% Elevation + 10% Traffic + 5% Drainage
        """
        info = ROAD_FLOOD_REGISTRY.get(road_name, {
            "road_id": "R100",
            "latitude": 13.0827,
            "longitude": 80.2707,
            "elevation_meters": 7.0,
            "historical_flood_risk": "MEDIUM",
            "historical_flood_score": 40,
            "drainage_condition": "FAIR",
            "drainage_score": 40,
            "alternate_route": "Ring Road"
        })

        elevation = override_elevation if override_elevation is not None else info["elevation_meters"]

        # 1. Rainfall Score (0 - 100)
        if rainfall_mm_per_hour == 0:
            s_rain = 0.0
        elif rainfall_mm_per_hour < 10:
            s_rain = 25.0
        elif rainfall_mm_per_hour < 30:
            s_rain = 55.0
        elif rainfall_mm_per_hour < 60:
            s_rain = 80.0
        else:
            s_rain = 100.0

        # 2. Historical Flood Score (0 - 100)
        s_hist = float(info["historical_flood_score"])

        # 3. Water Level Sensor Score (0 - 100)
        water_level_display = "UNAVAILABLE"
        if sensor_water_level_cm is not None:
            water_level_display = f"{sensor_water_level_cm:.1f} cm"
            if sensor_water_level_cm < 5:
                s_water = 10.0
            elif sensor_water_level_cm < 15:
                s_water = 45.0
            elif sensor_water_level_cm < 30:
                s_water = 75.0
            else:
                s_water = 100.0
        else:
            # If sensor unavailable, use rainfall-estimated virtual gauge for baseline scoring
            s_water = min(100.0, s_rain * 0.8)

        # 4. Elevation Score (0 - 100): Lower elevation = Higher Risk
        if elevation <= 4.0:
            s_elev = 95.0
        elif elevation <= 6.0:
            s_elev = 80.0
        elif elevation <= 10.0:
            s_elev = 40.0
        elif elevation <= 15.0:
            s_elev = 15.0
        else:
            s_elev = 0.0

        # 5. Traffic Speed/Density Score (Slowing traffic increases risk weight)
        if vehicle_speed < 15.0 or traffic_density in ["HIGH", "CRITICAL"]:
            s_traffic = 90.0
        elif vehicle_speed < 30.0 or traffic_density == "MEDIUM":
            s_traffic = 50.0
        else:
            s_traffic = 10.0

        # 6. Drainage Score
        s_drain = float(info["drainage_score"])

        # Calculate Total Weighted Flood Risk Score (0 - 100)
        raw_score = (
            cls.WEIGHTS["rainfall"] * s_rain +
            cls.WEIGHTS["history"] * s_hist +
            cls.WEIGHTS["water_level"] * s_water +
            cls.WEIGHTS["elevation"] * s_elev +
            cls.WEIGHTS["traffic"] * s_traffic +
            cls.WEIGHTS["drainage"] * s_drain
        )

        flood_risk_score = min(100, max(0, int(round(raw_score))))

        # Classify Risk Level & Road Safety Status
        if flood_risk_score <= 20:
            risk_level = "LOW"
            road_status = "SAFE"
            pred_waterlogging = False
            eta_waterlogging = "None"
            action = "Road is safe. Continue standard traffic operations."
        elif flood_risk_score <= 40:
            risk_level = "MODERATE"
            road_status = "MONITOR"
            pred_waterlogging = False
            eta_waterlogging = "60+ minutes"
            action = "Monitor rainfall and road drainage. Prepare potential traffic alerts."
        elif flood_risk_score <= 60:
            risk_level = "HIGH"
            road_status = "HIGH RISK"
            pred_waterlogging = True
            eta_waterlogging = "45 minutes"
            action = "Prepare alternate route diversion. Pre-alert signal controllers."
        elif flood_risk_score <= 80:
            risk_level = "VERY HIGH"
            road_status = "VERY HIGH RISK"
            pred_waterlogging = True
            eta_waterlogging = "30 minutes"
            action = "Issue citizen warnings. Divert traffic to alternate route and optimize signal timings."
        else:
            risk_level = "CRITICAL"
            road_status = "FLOODED"
            pred_waterlogging = True
            eta_waterlogging = "15 minutes (WATERLOGGING IMMINENT / ACTIVE)"
            action = "Avoid road! Issue immediate Voice AI and WhatsApp emergency alerts. Divert all traffic to alternate route."

        # Early Warning Timeline Steps
        timeline = [
            {"time": "NOW", "step": "Heavy Rainfall / Runoff Ingress", "status": f"Rainfall: {rainfall_mm_per_hour} mm/hr"},
            {"time": "10 MIN", "step": "Traffic Speed Sinks & Surface Pooling", "status": f"Predicted Speed: {max(10, vehicle_speed*0.6):.1f} km/h"},
            {"time": "20 MIN", "step": "Drainage Saturation & Waterlogging Surge", "status": f"Flood Risk: {flood_risk_score}%"},
            {"time": eta_waterlogging.split()[0] if pred_waterlogging else "35 MIN", "step": "Severe Waterlogging / Inundation", "status": f"Action: {info['alternate_route']}"}
        ]

        # Predicted Congestion Surge Impact
        baseline_congestion = 45 if traffic_density == "MEDIUM" else (80 if traffic_density in ["HIGH", "CRITICAL"] else 20)
        predicted_congestion = min(100, baseline_congestion + (35 if flood_risk_score > 60 else 15))

        return {
            "record_id": f"FLD-{road_name.replace(' ', '').upper()[:4]}-{int(rainfall_mm_per_hour)}",
            "road_id": info["road_id"],
            "road_name": road_name,
            "location": {
                "latitude": info["latitude"],
                "longitude": info["longitude"]
            },
            "rainfall_mm_per_hour": rainfall_mm_per_hour,
            "weather_condition": weather_condition,
            "road_elevation_meters": elevation,
            "historical_flood_risk": info["historical_flood_risk"],
            "drainage_condition": info["drainage_condition"],
            "water_level": water_level_display,
            "traffic_density": traffic_density,
            "vehicle_speed_kmh": vehicle_speed,
            "flood_risk_score": flood_risk_score,
            "risk_level": risk_level,
            "road_status": road_status,
            "predicted_waterlogging": pred_waterlogging,
            "estimated_time_to_waterlogging": eta_waterlogging,
            "predicted_congestion_pct": predicted_congestion,
            "recommended_action": action,
            "alternate_route": info["alternate_route"],
            "early_warning_timeline": timeline,
            "decision_factors": [
                f"Rainfall intensity: {rainfall_mm_per_hour} mm/hr (Weight 30%)",
                f"Road elevation: {elevation}m ({'Low-lying flood hazard' if elevation < 6 else 'Adequate elevation'})",
                f"Historical flood risk: {info['historical_flood_risk']} zone (Weight 20%)",
                f"Traffic speed: {vehicle_speed} km/h with {traffic_density} density",
                f"Drainage status: {info['drainage_condition']}"
            ]
        }


@tool("evaluate_flood_and_waterlogging_tool")
def evaluate_flood_and_waterlogging_tool(road_name: str, rainfall_mm: float = 45.0, speed_kmh: float = 25.0) -> str:
    """
    Evaluates road flood risk score (0-100), predicts waterlogging time, and recommends alternate detour routes.
    """
    res = FloodRiskCalculator.calculate_risk(
        road_name=road_name,
        rainfall_mm_per_hour=rainfall_mm,
        vehicle_speed=speed_kmh
    )
    return json.dumps(res, indent=2)
