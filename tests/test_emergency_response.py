"""
Unit & Scenario Test Suite for Emergency Traffic Response Workflow.
Verifies 5 complete emergency scenarios: Normal, Heavy Traffic, Accident, Critical Ambulance, and Recovery.
"""

import unittest
from crew import run_traffic_crew


class TestEmergencyResponseWorkflow(unittest.TestCase):
    """Test suite covering the 5 required emergency response scenarios."""

    def test_scenario_1_normal_traffic(self):
        """TEST 1: Normal traffic flow -> Normal signals, no emergency audio."""
        telemetry = {
            "road": "Main Road",
            "vehicle_count": 40,
            "average_speed": 55.0,
            "accident": False,
            "emergency_vehicle": False
        }
        res = run_traffic_crew(telemetry)
        e_corr = res["emergency_corridor"]
        s_opt = res["signal_optimization"]

        self.assertFalse(e_corr["emergency_detected"])
        self.assertFalse(e_corr["green_corridor_active"])
        self.assertEqual(e_corr["event_type"], "NORMAL")
        self.assertEqual(s_opt["recommended_green_time_sec"], 30)
        self.assertEqual(s_opt["recommended_red_time_sec"], 30)

    def test_scenario_2_heavy_traffic(self):
        """TEST 2: Heavy traffic -> Adaptive signal optimization."""
        telemetry = {
            "road": "Broadway Ave",
            "vehicle_count": 160,
            "average_speed": 18.0,
            "road_occupancy_pct": 82.0,
            "accident": False,
            "emergency_vehicle": False
        }
        res = run_traffic_crew(telemetry)
        e_corr = res["emergency_corridor"]
        s_opt = res["signal_optimization"]

        self.assertEqual(e_corr["event_type"], "HIGH TRAFFIC")
        self.assertGreaterEqual(s_opt["recommended_green_time_sec"], 65)

    def test_scenario_3_accident_detected(self):
        """TEST 3: Accident detected -> Signal adjustment (+20s), voice alert, citizen alert."""
        telemetry = {
            "road": "Express Highway",
            "vehicle_count": 80,
            "average_speed": 25.0,
            "accident": True,
            "accident_status": True,
            "emergency_vehicle": False
        }
        res = run_traffic_crew(telemetry)
        e_corr = res["emergency_corridor"]
        s_opt = res["signal_optimization"]
        c_alt = res["citizen_alerts"]

        self.assertTrue(e_corr["emergency_detected"])
        self.assertIn(e_corr["event_type"], ["ACCIDENT", "CRITICAL ACCIDENT"])
        self.assertGreaterEqual(s_opt["recommended_green_time_sec"], 50)
        self.assertLessEqual(s_opt["recommended_red_time_sec"], 15)
        self.assertIn(c_alt["severity"], ["CRITICAL", "EMERGENCY"])
        self.assertIn("voice_script", e_corr)
        self.assertIn("accident has been detected", e_corr["voice_script"])


    def test_scenario_4_critical_accident_with_ambulance(self):
        """TEST 4: Critical accident + Ambulance -> Green Corridor, priority voice AI, DB event."""
        telemetry = {
            "road": "Downtown Ring",
            "vehicle_count": 175,
            "average_speed": 12.0,
            "accident": True,
            "emergency_vehicle": True,
            "emergency_type": "Ambulance"
        }
        res = run_traffic_crew(telemetry)
        e_corr = res["emergency_corridor"]
        s_opt = res["signal_optimization"]
        c_alt = res["citizen_alerts"]

        self.assertTrue(e_corr["emergency_detected"])
        self.assertTrue(e_corr["green_corridor_active"])
        self.assertEqual(e_corr["event_type"], "MEDICAL EMERGENCY")
        self.assertEqual(s_opt["recommended_green_time_sec"], 90)
        self.assertIn("ambulance is approaching", e_corr["voice_script"])
        self.assertEqual(c_alt["severity"], "EMERGENCY")

    def test_scenario_5_emergency_resolved_recovery(self):
        """TEST 5: Emergency resolved -> Green corridor OFF, normal signals restored, resolution voice alert."""
        telemetry = {
            "road": "Harbor View Park",
            "accident": False,
            "emergency_vehicle": False,
            "accident_resolved": True,
            "emergency_vehicle_passed": True
        }
        res = run_traffic_crew(telemetry)
        e_corr = res["emergency_corridor"]
        s_opt = res["signal_optimization"]
        c_alt = res["citizen_alerts"]

        self.assertFalse(e_corr["green_corridor_active"])
        self.assertEqual(e_corr["event_type"], "NORMAL")
        self.assertEqual(s_opt["recommended_green_time_sec"], 30)
        self.assertEqual(s_opt["recommended_red_time_sec"], 30)
        self.assertIn("resolved", e_corr["voice_script"])
        self.assertIn("RESOLVED", c_alt["title"])


if __name__ == "__main__":
    unittest.main()
