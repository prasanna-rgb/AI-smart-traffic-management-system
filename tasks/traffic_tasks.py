"""
CrewAI Task definitions for Smart Traffic Agents.
"""
try:
    from crewai import Task
except Exception:
    Task = None


def create_traffic_tasks(agents_dict: dict, telemetry_input: dict) -> list:
    """
    Creates sequential CrewAI tasks mapped to agents.
    
    Args:
        agents_dict: Dictionary containing instantiated CrewAI agents.
        telemetry_input: Telemetry dictionary for the monitored road.
    
    Returns:
        List of configured CrewAI Task objects.
    """
    input_str = str(telemetry_input)

    # Task 1: Traffic Monitoring
    task_monitor = Task(
        description=f"Analyze raw traffic telemetry input: {input_str}. Generate standard JSON Traffic Report with density classification.",
        expected_output="JSON object containing road name, vehicle count, density, average speed, accident, emergency vehicle status, and weather.",
        agent=agents_dict["monitor"]
    )

    tasks_list = [task_monitor]

    # Task 2: Driver Behavior & Safety Analytics (if present)
    if "driver_safety" in agents_dict:
        task_driver_safety = Task(
            description=f"Analyze driver & vehicle behavior from telemetry: {input_str}. Detect 8 violation categories, calculate Driver Safety Score (0-100), predict risk probability, and issue safety alerts.",
            expected_output="JSON object with vehicle_id, safety_score, risk_level, violations, primary_hazard, recommendation, risk_prediction, and formatted_alert.",
            agent=agents_dict["driver_safety"]
        )
        tasks_list.append(task_driver_safety)

    # Task 3: Congestion Prediction
    task_congestion = Task(
        description="Read Traffic Report from Task 1. Calculate congestion score (0-100), predict 30-min traffic trend, and recommend alternate bypass roads.",
        expected_output="JSON object containing congestion score, risk level, predicted trend, estimated delay, and alternate routes.",
        agent=agents_dict.get("congestion", agents_dict.get("prediction"))
    )
    tasks_list.append(task_congestion)

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

