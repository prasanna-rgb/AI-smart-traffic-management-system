"""
Specialized Agent: Driver Behavior & Safety Analytics Agent (Backend Package).
Continuously analyzes driver and vehicle telemetry to detect 8 violation types,
computes Driver Safety Score (0-100), risk levels, risk predictions, location intelligence, and safety alerts.
"""

from typing import Dict, Any
from agents.driver_safety_agent import (
    create_driver_safety_agent,
    process_driver_safety_rule_based
)

__all__ = ["create_driver_safety_agent", "process_driver_safety_rule_based"]
