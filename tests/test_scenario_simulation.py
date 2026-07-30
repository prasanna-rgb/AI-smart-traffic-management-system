"""
Unit Test Suite for Traffic Scenario Simulation & Decision Agent.
Verifies 5 complete test cases: Normal Traffic, Heavy Congestion, Accident, Critical Accident + Ambulance, and Road Closure.
"""

import unittest
from crew import run_traffic_crew
from tools.scenario_simulation_tools import ScenarioSimulator


class TestScenarioSimulationAgent(unittest.TestCase):
    """Test suite covering the 5 required scenario simulation test cases."""

    def test_scenario_1_normal_traffic(self):
        """TEST 1: Normal Traffic -> AI recommends normal adaptive signal operation."""
        telemetry = {
            "road": "Main Road",
            "vehicle_count": 35,
            "average_speed": 55.0,
            "accident": False,
            "emergency_vehicle": False
        }
        res = run_traffic_crew(telemetry)
        scen = res.get("scenario_simulation", {})

        self.assertIn("winning_scenario_id", scen)
        self.assertGreaterEqual(scen["decision_score"], 50.0)
        self.assertLessEqual(scen["expected_congestion"], 50)
        self.assertEqual(scen["expected_carbon_emission"], "LOW")

    def test_scenario_2_heavy_congestion(self):
        """TEST 2: Heavy Congestion -> AI compares signal optimization & traffic diversion."""
        telemetry = {
            "road": "Broadway Ave",
            "vehicle_count": 180,
            "average_speed": 16.0,
            "road_occupancy_pct": 85.0,
            "accident": False,
            "emergency_vehicle": False
        }
        res = run_traffic_crew(telemetry)
        scen = res.get("scenario_simulation", {})

        self.assertIn("scenarios_evaluated", scen)
        self.assertGreaterEqual(len(scen["scenarios_evaluated"]), 3)
        self.assertGreaterEqual(scen["decision_score"], 60.0)
        self.assertLess(scen["expected_congestion"], 85)

    def test_scenario_3_accident(self):
        """TEST 3: Accident -> AI evaluates traffic diversion and signal changes."""
        telemetry = {
            "road": "Express Highway",
            "vehicle_count": 95,
            "average_speed": 20.0,
            "accident": True,
            "emergency_vehicle": False
        }
        res = run_traffic_crew(telemetry)
        scen = res.get("scenario_simulation", {})

        self.assertIn("scenarios_evaluated", scen)
        self.assertGreaterEqual(scen["decision_score"], 65.0)
        self.assertIn("reason", scen)

    def test_scenario_4_critical_accident_with_ambulance(self):
        """TEST 4: Critical Accident + Ambulance -> AI simulates & selects Emergency Green Corridor."""
        telemetry = {
            "road": "Downtown Ring",
            "vehicle_count": 175,
            "average_speed": 12.0,
            "accident": True,
            "emergency_vehicle": True,
            "emergency_type": "Ambulance"
        }
        res = run_traffic_crew(telemetry)
        scen = res.get("scenario_simulation", {})
        e_corr = res.get("emergency_corridor", {})
        s_opt = res.get("signal_optimization", {})

        self.assertTrue(e_corr["green_corridor_active"])
        self.assertGreaterEqual(scen["decision_score"], 80.0)
        self.assertLessEqual(scen["emergency_response_time"], 5)
        self.assertIn("Green Corridor", scen["recommended_action"])

    def test_scenario_5_road_closure(self):
        """TEST 5: Road Closure -> AI evaluates alternate routes."""
        telemetry = {
            "road": "Harbor View Park",
            "vehicle_count": 140,
            "average_speed": 15.0,
            "accident": True,
            "road_status": "CLOSED"
        }
        res = run_traffic_crew(telemetry)
        scen = res.get("scenario_simulation", {})

        self.assertIn("scenarios_evaluated", scen)
        self.assertGreaterEqual(scen["decision_score"], 60.0)


if __name__ == "__main__":
    unittest.main()
