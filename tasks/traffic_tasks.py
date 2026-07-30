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

    # Task 2: Congestion Prediction
    task_congestion = Task(
        description="Read Traffic Report from Task 1. Calculate congestion score (0-100), predict 30-min traffic trend, and recommend alternate bypass roads.",
        expected_output="JSON object containing congestion score, risk level, predicted trend, estimated delay, and alternate routes.",
        agent=agents_dict["congestion"]
    )

    # Task 3: Emergency Vehicle Priority
    task_emergency = Task(
        description="Inspect Traffic Report & Congestion data. If emergency vehicles (Ambulance/Fire Truck/Police) are present, generate Green Corridor route and signal override commands.",
        expected_output="JSON object with green corridor status, vehicle type, priority route, and signal override instructions.",
        agent=agents_dict["emergency"]
    )

    # Task 4: Signal Optimization
    task_signal = Task(
        description="Synthesize reports from previous tasks. Compute optimal dynamic green light duration (e.g. +15s to +60s) to reduce wait times and clear queue bottleneck.",
        expected_output="JSON object with target junction, current/recommended green times, dynamic extension, and estimated wait reduction.",
        agent=agents_dict["signal"]
    )

    # Task 5: Citizen Communication
    task_citizen = Task(
        description="Formulate citizen warning notifications, road alerts, accident advisories, detour directions, and emergency corridor yielding notices.",
        expected_output="JSON object containing alert title, severity, human-readable message, affected road, and broadcast channels.",
        agent=agents_dict["citizen"]
    )

    # Task 6: Traffic Analytics
    task_analytics = Task(
        description="Aggregate overall system decisions. Calculate road performance score (0-100), estimate CO2 carbon emissions, and output executive insights.",
        expected_output="JSON object containing performance index, carbon emissions (kg CO2), and summary key insights.",
        agent=agents_dict["analytics"]
    )

    return [task_monitor, task_congestion, task_emergency, task_signal, task_citizen, task_analytics]
