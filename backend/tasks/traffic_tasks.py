"""
CrewAI Task Definitions for the 6-Agent Smart Traffic Pipeline.
"""
from typing import Dict, Any, List

try:
    from crewai import Task
    CREWAI_AVAILABLE = True
except Exception:
    CREWAI_AVAILABLE = False
    Task = None

def create_traffic_tasks(agents: Dict[str, Any], telemetry_input: Dict[str, Any]) -> List:
    """Creates sequential task objects for all 6 CrewAI agents if CrewAI is loaded."""
    if not CREWAI_AVAILABLE or Task is None:
        return []
        
    t_vision = Task(
        description=f"Analyze raw camera stream telemetry for intersection {telemetry_input.get('road', 'INT-01')}: {telemetry_input}. Count cars, buses, trucks, motorcycles, and ambulances.",
        expected_output="JSON object containing exact fleet composition counts, density percentage, and emergency vehicle status.",
        agent=agents.get("vision")
    )

    t_analysis = Task(
        description="Evaluate vision metrics to calculate Level of Service (LOS A-F), vehicle queue length, occupancy rate, and identify bottleneck congestion points.",
        expected_output="JSON object with LOS grade, average delay seconds, and queue length in meters.",
        agent=agents.get("traffic_analysis")
    )

    t_prediction = Task(
        description="Forecast 5, 10, 15, and 30-minute congestion score trends based on current inflow and analysis metrics.",
        expected_output="JSON object with 5m, 10m, 15m, 30m forecast scores and trend narrative.",
        agent=agents.get("prediction")
    )

    t_pollution = Task(
        description="Calculate environmental impact metrics including CO2 (kg/hr), NOx (g/hr), PM2.5 (g/hr), and fuel consumption rates.",
        expected_output="JSON object with CO2 emissions, NOx, PM2.5, fuel burn rate, and Eco Index score.",
        agent=agents.get("pollution")
    )

    t_emergency = Task(
        description="Check for emergency vehicles and determine green corridor routing across connected intersections.",
        expected_output="JSON object with emergency status, priority score (1-10), and green corridor path list.",
        agent=agents.get("emergency")
    )

    t_decision = Task(
        description="Reason over all previous agent outputs to determine optimal green signal timing splits and generate natural language explainable AI (XAI) decision rationale.",
        expected_output="JSON object with optimized signal timing splits, active phase, and detailed natural language XAI decision reasoning.",
        agent=agents.get("decision")
    )

    return [t_vision, t_analysis, t_prediction, t_pollution, t_emergency, t_decision]
