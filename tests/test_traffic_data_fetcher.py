"""
Unit & Integration Test Suite for Traffic Data Fetcher, Validation, Tooling, and Data Lineage.
"""

import unittest
import json
from tools.traffic_data_fetcher import (
    TrafficDataFetcher,
    TrafficDataValidator,
    fetch_traffic_data,
    get_data_lineage
)
from agents.traffic_monitor import process_traffic_monitor_rule_based
from tasks.traffic_tasks import create_traffic_tasks


class TestTrafficDataFetcher(unittest.TestCase):
    """Test suite covering traffic data fetching, validation bounds, tools, and debug lineage."""

    def test_successful_traffic_data_fetch(self):
        """Test fetching structured traffic data for supported road."""
        data = TrafficDataFetcher.get_traffic_data("Main Road")
        self.assertIsNotNone(data)
        self.assertEqual(data["road_name"], "Main Road")
        self.assertEqual(data["road_id"], "R001")
        self.assertIn("vehicle_count", data)
        self.assertIn("average_speed", data)
        self.assertIn("traffic_density", data)
        self.assertIn("congestion_level", data)
        self.assertIn("travel_time", data)

    def test_data_validation_bounds(self):
        """Test TrafficDataValidator enforces bounds on valid data."""
        raw_sample = {
            "road_id": "R001",
            "road_name": "Main Road",
            "latitude": 13.0827,
            "longitude": 80.2707,
            "vehicle_count": 142,
            "average_speed": 24.5,
            "traffic_density": "HIGH",
            "congestion_level": 82,
            "travel_time": 18,
            "normal_travel_time": 8,
            "delay": 10,
            "accident_status": False,
            "emergency_vehicle_status": False,
            "road_status": "OPEN",
            "weather": "CLEAR"
        }
        validated = TrafficDataValidator.validate_and_sanitize(raw_sample)
        self.assertEqual(validated["vehicle_count"], 142)
        self.assertEqual(validated["average_speed"], 24.5)
        self.assertEqual(validated["congestion_level"], 82)
        self.assertEqual(validated["latitude"], 13.0827)
        self.assertEqual(validated["longitude"], 80.2707)
        self.assertEqual(validated["delay"], 10)

    def test_invalid_and_missing_values_sanitization(self):
        """Test out-of-bounds coordinates and missing values are sanitized to 'unavailable' without crashing."""
        corrupted_sample = {
            "vehicle_count": -5,
            "average_speed": -10.0,
            "congestion_level": None,
            "latitude": 195.0, # invalid lat
            "longitude": -200.0, # invalid lng
            "travel_time": -1
        }
        sanitized = TrafficDataValidator.validate_and_sanitize(corrupted_sample)
        self.assertEqual(sanitized["vehicle_count"], "unavailable")
        self.assertEqual(sanitized["average_speed"], "unavailable")
        self.assertEqual(sanitized["congestion_level"], "unavailable")
        self.assertEqual(sanitized["latitude"], "unavailable")
        self.assertEqual(sanitized["longitude"], "unavailable")
        self.assertEqual(sanitized["travel_time"], "unavailable")

    def test_crewai_tool_invocation(self):
        """Test fetch_traffic_data CrewAI tool returns valid JSON string."""
        raw_json_output = fetch_traffic_data("Express Highway")
        self.assertIsInstance(raw_json_output, str)
        parsed = json.loads(raw_json_output)
        self.assertEqual(parsed["road_name"], "Express Highway")
        self.assertEqual(parsed["road_id"], "R003")

    def test_traffic_monitoring_agent_structured_output(self):
        """Test Traffic Monitoring Agent produces valid structured JSON report."""
        raw_data = TrafficDataFetcher.get_traffic_data("Broadway Ave")
        agent_report = process_traffic_monitor_rule_based(raw_data)
        
        self.assertEqual(agent_report["road_name"], "Broadway Ave")
        self.assertIn("location", agent_report)
        self.assertIn("latitude", agent_report["location"])
        self.assertIn("longitude", agent_report["location"])
        self.assertIn("vehicle_count", agent_report)
        self.assertIn("average_speed", agent_report)
        self.assertIn("traffic_density", agent_report)
        self.assertIn("congestion_level", agent_report)
        self.assertIn("risk_level", agent_report)

    def test_data_lineage_trace(self):
        """Test get_data_lineage produces 5-stage debug trace."""
        lineage = get_data_lineage("Main Road")
        self.assertIn("data_source", lineage)
        self.assertIn("raw_response", lineage)
        self.assertIn("normalized_response", lineage)
        self.assertIn("agent_input", lineage)
        self.assertIn("agent_output", lineage)
        self.assertIn("TRAFFIC DATA:", lineage["agent_input"])

    def test_task_creation_prompt_formatting(self):
        """Test create_traffic_tasks injects structured traffic metrics into task prompt."""
        import tasks.traffic_tasks as tt
        class DummyTask:
            def __init__(self, description, expected_output, agent):
                self.description = description
                self.expected_output = expected_output
                self.agent = agent
        
        orig_task = tt.Task
        tt.Task = DummyTask
        try:
            agents_dict = {"monitor": None}
            tasks_list = tt.create_traffic_tasks(agents_dict, {"road": "Downtown Ring"})
            self.assertEqual(len(tasks_list), 1)
            self.assertIn("TRAFFIC DATA:", tasks_list[0].description)
            self.assertIn("Road Name: Downtown Ring", tasks_list[0].description)
        finally:
            tt.Task = orig_task



if __name__ == "__main__":
    unittest.main()
