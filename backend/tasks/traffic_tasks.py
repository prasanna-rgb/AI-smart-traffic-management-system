"""
CrewAI Task definitions for Smart Traffic Agents (Backend Package).
Configures structured task prompts, expected outputs, and data passing pipelines.
"""

from typing import Dict, Any, List
try:
    from crewai import Task
except Exception:
    Task = None

from backend.tools.traffic_data_fetcher import TrafficDataFetcher


def create_traffic_tasks(agents_dict: dict, telemetry_input: dict) -> list:
    """
    Creates sequential CrewAI tasks mapped to agents.
    
    Args:
        agents_dict: Dictionary containing instantiated CrewAI agents.
        telemetry_input: Raw or pre-processed telemetry dictionary for the monitored road.
    
    Returns:
        List of configured CrewAI Task objects.
    """
    if Task is None:
        return []

    road_name = telemetry_input.get("road_name", telemetry_input.get("road", "Main Road"))

    traffic_struct = TrafficDataFetcher.get_traffic_data(road_name)

    # Override with explicitly injected custom telemetry parameters if provided
    for k, v in telemetry_input.items():
        if k in ["vehicle_count", "vehicles", "average_speed", "accident", "emergency_vehicle", "weather"]:
            if k == "vehicles":
                traffic_struct["vehicle_count"] = v
            elif k == "accident":
                traffic_struct["accident_status"] = bool(v)
            elif k == "emergency_vehicle":
                traffic_struct["emergency_vehicle_status"] = bool(v)
            else:
                traffic_struct[k] = v

    # Formulate complete structured prompt
    input_prompt = (
        f"TRAFFIC DATA:\n"
        f"Road ID: {traffic_struct.get('road_id')}\n"
        f"Road Name: {traffic_struct.get('road_name')}\n"
        f"Latitude: {traffic_struct.get('latitude')}\n"
        f"Longitude: {traffic_struct.get('longitude')}\n"
        f"Vehicle Count: {traffic_struct.get('vehicle_count')}\n"
        f"Average Speed: {traffic_struct.get('average_speed')} km/h\n"
        f"Traffic Density: {traffic_struct.get('traffic_density')}\n"
        f"Congestion Level: {traffic_struct.get('congestion_level')}%\n"
        f"Travel Time: {traffic_struct.get('travel_time')} minutes\n"
        f"Normal Travel Time: {traffic_struct.get('normal_travel_time')} minutes\n"
        f"Delay: {traffic_struct.get('delay')} minutes\n"
        f"Accident Status: {traffic_struct.get('accident_status')}\n"
        f"Emergency Vehicle Status: {traffic_struct.get('emergency_vehicle_status')}\n"
        f"Road Status: {traffic_struct.get('road_status')}\n"
        f"Weather: {traffic_struct.get('weather')}\n"
        f"Timestamp: {traffic_struct.get('timestamp')}"
    )

    tasks_list = []

    # Task 1: Traffic Monitoring
    if "monitor" in agents_dict:
        task_monitor = Task(
            description=(
                f"You are provided with real structured traffic data:\n\n{input_prompt}\n\n"
                f"Validate metrics, analyze traffic conditions, diagnose bottlenecks or emergency events, "
                f"and generate a standard structured JSON Traffic Report. "
                f"DO NOT invent or hallucinate metrics. Use 'unavailable' for any unprovided values."
            ),
            expected_output=(
                "Structured JSON object with keys: road_id, road_name, location (latitude, longitude), "
                "vehicle_count, average_speed, traffic_density, congestion_level, travel_time, delay, "
                "accident_status, emergency_vehicle_status, road_status, weather, timestamp, risk_level."
            ),
            agent=agents_dict["monitor"]
        )
        tasks_list.append(task_monitor)

    # Task 2: Driver Behavior & Safety Analytics
    if "driver_safety" in agents_dict:
        task_driver_safety = Task(
            description=(
                f"Analyze driver behavior telemetry for {road_name}.\n\n{input_prompt}\n\n"
                f"Detect 8 violation categories, compute Driver Safety Score (0-100), classify Risk Level, "
                f"predict risk probability, and generate safety alerts."
            ),
            expected_output=(
                "JSON object with vehicle_id, safety_score, risk_level, violations, primary_hazard, "
                "recommendation, risk_prediction, and formatted_alert."
            ),
            agent=agents_dict["driver_safety"]
        )
        tasks_list.append(task_driver_safety)

    # Task 3: Congestion Prediction
    if "congestion" in agents_dict or "prediction" in agents_dict:
        task_congestion = Task(
            description="Read Traffic Report from Task 1. Calculate congestion score (0-100), predict 30-min traffic trend, and recommend alternate bypass roads.",
            expected_output="JSON object containing congestion score, risk level, predicted trend, estimated delay, and alternate routes.",
            agent=agents_dict.get("congestion", agents_dict.get("prediction"))
        )
        tasks_list.append(task_congestion)

    # Task 3.5: Scenario Simulation & Decision Intelligence
    if "scenario_simulation" in agents_dict:
        task_scenario = Task(
            description=(
                f"Simulate candidate traffic management strategies for {road_name}.\n\n{input_prompt}\n\n"
                f"Ask 'What will happen if I take this action?', generate candidate scenarios (maintain timing, green extension, emergency corridor, alternate route diversion), "
                f"calculate predicted metrics (congestion, speed, wait time, delay, emergency response, carbon emissions), "
                f"compute weighted decision scores (0-100), and recommend the winning action."
            ),
            expected_output=(
                "JSON object with recommended_action, decision_score, expected_congestion, expected_delay, "
                "emergency_response_time, expected_carbon_emission, confidence, reason, and scenarios_evaluated."
            ),
            agent=agents_dict["scenario_simulation"]
        )
        tasks_list.append(task_scenario)

    # Task 3.7: Emergency Resource Allocation
    if "emergency_resource" in agents_dict:
        task_emergency_resource = Task(
            description=(
                f"Evaluate accident information for {road_name}.\n\n{input_prompt}\n\n"
                f"Fetch available fleet ambulances and nearby regional hospitals. Evaluate multi-attribute suitability scores based on "
                f"travel time, traffic conditions, medical capability, ICU bed availability, and trauma center status. "
                f"Select optimal ambulance and hospital, calculate total emergency response time (Ambulance ETA + Hospital ETA), and recommend optimal rescue route."
            ),
            expected_output=(
                "JSON object with selected_ambulance, selected_hospital, total_estimated_time, "
                "recommended_route, decision_score, reason, ambulance_options, and hospital_options."
            ),
            agent=agents_dict["emergency_resource"]
        )
        tasks_list.append(task_emergency_resource)

    # Task 4: Emergency Vehicle Priority
    if "emergency" in agents_dict:
        task_emergency = Task(
            description="Inspect Traffic Report & Congestion data. If emergency vehicles are present, generate Green Corridor route and signal override commands.",
            expected_output="JSON object with green corridor status, vehicle type, priority route, and signal override instructions.",
            agent=agents_dict["emergency"]
        )
        tasks_list.append(task_emergency)

    # Task 5: Signal Optimization / Decision
    signal_agent = agents_dict.get("signal", agents_dict.get("decision"))
    if signal_agent:
        task_signal = Task(
            description="Synthesize reports from previous tasks. Compute optimal dynamic green light duration to reduce wait times and clear queue bottleneck.",
            expected_output="JSON object with target junction, current/recommended green times, dynamic extension, and estimated wait reduction.",
            agent=signal_agent
        )
        tasks_list.append(task_signal)

    # Task 6: Citizen Communication
    if "citizen" in agents_dict:
        task_citizen = Task(
            description="Formulate citizen warning notifications, road alerts, driver safety warnings, accident advisories, detour directions, and emergency corridor yielding notices.",
            expected_output="JSON object containing alert title, severity, human-readable message, affected road, and broadcast channels.",
            agent=agents_dict["citizen"]
        )
        tasks_list.append(task_citizen)

    # Task 7: Traffic Analytics
    if "analytics" in agents_dict:
        task_analytics = Task(
            description="Aggregate overall system decisions and driver safety metrics. Calculate road performance score (0-100), estimate CO2 carbon emissions, and output executive insights.",
            expected_output="JSON object containing performance index, carbon emissions (kg CO2), and summary key insights.",
            agent=agents_dict["analytics"]
        )
        tasks_list.append(task_analytics)

    return tasks_list
