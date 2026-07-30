"""
Pollution Agent: Estimates carbon emissions (CO2, NOx, PM2.5) and fuel consumption based on fleet mix and idling times.
"""
from typing import Dict, Any
from config.settings import get_llm

try:
    from crewai import Agent
    CREWAI_AVAILABLE = True
except Exception:
    CREWAI_AVAILABLE = False
    Agent = None

def create_pollution_agent():
    if not CREWAI_AVAILABLE:
        return None
    llm = get_llm()
    return Agent(
        role="Environmental Impact & Urban Emissions Scientist",
        goal="Quantify real-time carbon emissions (CO2 kg/hr), particulate pollutants (NOx, PM2.5), and fuel burn rate based on detected vehicle types and congestion idling.",
        backstory="""You are an Urban Environmental Health and Air Quality Specialist. You model greenhouse gas and tailpipe emissions using vehicle fleet composition, traffic stop-and-go patterns, and idling ratios.""",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

def process_pollution_rule_based(vision_output: Dict[str, Any], analysis_output: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic rule engine for Pollution Agent emission calculation."""
    breakdown = vision_output.get("fleet_breakdown", {})
    cars = breakdown.get("car", 30)
    buses = breakdown.get("bus", 2)
    trucks = breakdown.get("truck", 2)
    motorcycles = breakdown.get("motorcycle", 5)
    ambulances = breakdown.get("ambulance", 0)

    density_pct = vision_output.get("density_pct", 40.0)
    idling_multiplier = 1.0 + (density_pct / 100.0) * 1.5

    co2_rate = (cars * 2.3 + buses * 12.5 + trucks * 14.0 + motorcycles * 0.8 + ambulances * 3.5) * idling_multiplier
    nox_rate = (cars * 4.2 + buses * 35.0 + trucks * 45.0 + motorcycles * 1.5 + ambulances * 6.0) * idling_multiplier
    pm25_rate = (cars * 0.3 + buses * 2.8 + trucks * 3.5 + motorcycles * 0.15 + ambulances * 0.5) * idling_multiplier
    fuel_rate = (cars * 1.1 + buses * 5.2 + trucks * 5.8 + motorcycles * 0.35 + ambulances * 1.5) * idling_multiplier

    eco_index = max(10.0, min(100.0, round(100.0 - (co2_rate / 2.5), 1)))

    return {
        "intersection_code": vision_output.get("intersection_code", "INT-01"),
        "co2_kg_hr": round(co2_rate, 2),
        "nox_g_hr": round(nox_rate, 2),
        "pm25_g_hr": round(pm25_rate, 2),
        "fuel_liters_hr": round(fuel_rate, 2),
        "eco_index": eco_index,
        "idling_impact_multiplier": round(idling_multiplier, 2),
        "environmental_summary": f"Emissions operating at Eco-Index {eco_index}/100 with ~{round(co2_rate, 1)} kg CO2/hr emitted under current congestion levels."
    }
