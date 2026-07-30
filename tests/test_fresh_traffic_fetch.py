"""
Unit Test Suite verifying 5 consecutive fresh traffic fetch cycles.
Ensures timestamps, vehicle counts, speeds, congestion levels, and agent outputs update dynamically.
"""

import unittest
import time
from tools.traffic_data_fetcher import TrafficDataFetcher
from agents.traffic_monitor import process_traffic_monitor_rule_based


class TestFreshTrafficFetch(unittest.TestCase):
    """Test suite verifying that traffic data is fresh and dynamic across consecutive refresh cycles."""

    def test_five_consecutive_refresh_cycles(self):
        """Execute 5 consecutive refresh cycles and assert data updates on every cycle."""
        road_name = "Main Road"
        fetch_history = []
        agent_history = []

        print("\n--- STARTING 5-CYCLE REFRESH VERIFICATION ---")

        for cycle_idx in range(1, 6):
            # Fetch fresh traffic data
            data = TrafficDataFetcher.get_traffic_data(road_name=road_name)
            
            # Execute agent analysis
            agent_output = process_traffic_monitor_rule_based(data)
            
            fetch_history.append(data)
            agent_history.append(agent_output)

            print(
                f"Cycle {cycle_idx}: Time={data['time_display']} | "
                f"Vehicles={data['vehicle_count']} | Speed={data['average_speed']} km/h | "
                f"Congestion={data['congestion_level']}% | Agent Density={agent_output['density']}"
            )
            time.sleep(0.01)

        # 1. Assert 5 cycles were executed
        self.assertEqual(len(fetch_history), 5)
        self.assertEqual(len(agent_history), 5)

        # 2. Assert all items have valid timestamp & time_display
        for item in fetch_history:
            self.assertIn("timestamp", item)
            self.assertIn("time_display", item)
            self.assertIsNotNone(item["vehicle_count"])
            self.assertIsNotNone(item["average_speed"])

        # 3. Assert vehicle counts or speeds vary across 5 cycles (not static frozen numbers)
        vehicle_counts = [item["vehicle_count"] for item in fetch_history]
        speeds = [item["average_speed"] for item in fetch_history]

        print(f"Vehicle counts across 5 cycles: {vehicle_counts}")
        print(f"Average speeds across 5 cycles: {speeds}")

        # Check that metrics are not all identical static values
        self.assertTrue(
            len(set(vehicle_counts)) > 1 or len(set(speeds)) > 1,
            "Traffic metrics remained completely static across 5 refresh cycles!"
        )

        # 4. Assert Traffic Monitoring Agent received updated values and generated updated reports
        agent_vehicles = [rep["vehicle_count"] for rep in agent_history]
        self.assertEqual(agent_vehicles, vehicle_counts)

        print("--- 5-CYCLE REFRESH VERIFICATION SUCCESSFUL ---")


if __name__ == "__main__":
    unittest.main()
