"""
CrewAI Task definitions for Driver Behavior & Safety Analytics Agent.
"""

try:
    from crewai import Task
except Exception:
    Task = None


def create_driver_safety_task(agent, telemetry_input: dict):
    """
    Creates a CrewAI Task for Driver Behavior & Safety Analytics.
    
    Args:
        agent: Driver Behavior & Safety Analytics Agent instance.
        telemetry_input: Telemetry input dictionary.
        
    Returns:
        Configured CrewAI Task object or None if Task is unavailable.
    """
    if Task is None or agent is None:
        return None
        
    input_str = str(telemetry_input)
    return Task(
        description=(
            f"Analyze vehicle telemetry input: {input_str}. "
            "Detect 8 driver violation categories (Sudden Braking, Wrong-Way Driving, Overspeeding, Illegal U-Turns, "
            "Lane Violations, Dangerous Patterns, Repeated Violations). Calculate Driver Safety Score (0-100), "
            "classify Risk Level (LOW, MEDIUM, HIGH, CRITICAL), compute Driver Risk Prediction, log location intelligence, "
            "and generate safety audit alerts with actionable recommendations."
        ),
        expected_output=(
            "Structured JSON object with vehicle_id, safety_score, risk_level, violations breakdown, "
            "total_violations, location coordinates, primary_hazard, recommendation, risk_prediction, and formatted_alert."
        ),
        agent=agent
    )
