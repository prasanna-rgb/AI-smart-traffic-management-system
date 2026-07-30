"""
Unit & Integration Test Suite for Driver Behavior & Safety Analytics Agent.
Tests all 6 test cases and verifies exact output format, score calculations, risk levels, and DB persistence.
"""

import unittest
import json
from tools.driver_behavior_tools import DriverBehaviorTools
from agents.driver_safety_agent import process_driver_safety_rule_based
from database.db import init_db, save_driver_safety_log, get_driver_safety_logs


class TestDriverBehaviorSafetyAgent(unittest.TestCase):
    """Test suite for Driver Behavior & Safety Analytics Agent."""

    @classmethod
    def setUpClass(cls):
        init_db()
        cls.test_cases = DriverBehaviorTools.get_test_cases()

    def test_case_1_safe_driver(self):
        """Test Case 1: Safe Driver."""
        tc = self.test_cases[0]["telemetry"]
        res = process_driver_safety_rule_based(tc)
        
        self.assertEqual(res["vehicle_id"], "VH101")
        self.assertEqual(res["safety_score"], 100)
        self.assertEqual(res["risk_level"], "LOW")
        self.assertEqual(res["total_violations"], 0)
        self.assertEqual(res["risk_prediction"]["probability"], "LOW")

    def test_case_2_overspeeding_driver(self):
        """Test Case 2: Overspeeding Driver."""
        tc = self.test_cases[1]["telemetry"]
        res = process_driver_safety_rule_based(tc)
        
        self.assertEqual(res["vehicle_id"], "VH102")
        self.assertLess(res["safety_score"], 100)
        self.assertIn("overspeeding", res["violations"])
        self.assertGreater(res["violations"]["overspeeding"], 0)

    def test_case_3_frequent_sudden_braking(self):
        """Test Case 3: Frequent Sudden Braking."""
        tc = self.test_cases[2]["telemetry"]
        res = process_driver_safety_rule_based(tc)
        
        self.assertEqual(res["vehicle_id"], "VH103")
        self.assertEqual(res["violations"]["sudden_braking"], 6)
        self.assertIn(res["risk_level"], ["HIGH", "CRITICAL"])
        self.assertIn("sudden braking", res["primary_hazard"].lower())

    def test_case_4_wrong_way_driver(self):
        """Test Case 4: Wrong-Way Driver."""
        tc = self.test_cases[3]["telemetry"]
        res = process_driver_safety_rule_based(tc)
        
        self.assertEqual(res["vehicle_id"], "VH104")
        self.assertEqual(res["risk_level"], "CRITICAL")
        self.assertLessEqual(res["safety_score"], 65)
        self.assertIn("wrong-way", res["primary_hazard"].lower())

    def test_case_5_multiple_violations(self):
        """Test Case 5: Multiple Violations (exact prompt scenario)."""
        tc = self.test_cases[4]["telemetry"]
        res = process_driver_safety_rule_based(tc)
        
        self.assertEqual(res["vehicle_id"], "VH105")
        self.assertEqual(res["violations"]["sudden_braking"], 6)
        self.assertEqual(res["violations"]["overspeeding"], 1)
        self.assertEqual(res["violations"]["illegal_u_turn"], 4)
        self.assertEqual(res["violations"]["lane_violations"], 2)
        self.assertEqual(res["total_violations"], 13)
        self.assertEqual(res["risk_level"], "CRITICAL")
        self.assertIn("SAFETY INTELLIGENCE ALERT", res["formatted_alert"])

    def test_case_6_critical_risk_driver(self):
        """Test Case 6: Critical-Risk Driver."""
        tc = self.test_cases[5]["telemetry"]
        res = process_driver_safety_rule_based(tc)
        
        self.assertEqual(res["vehicle_id"], "VH106")
        self.assertEqual(res["risk_level"], "CRITICAL")
        self.assertLessEqual(res["safety_score"], 39)
        self.assertEqual(res["risk_prediction"]["probability"], "HIGH")

    def test_db_persistence(self):
        """Test saving and retrieving driver safety logs in DB."""
        tc = self.test_cases[4]["telemetry"]
        eval_res = process_driver_safety_rule_based(tc)
        
        saved = save_driver_safety_log(eval_res)
        self.assertIsNotNone(saved)
        
        logs = get_driver_safety_logs(limit=10)
        self.assertGreater(len(logs), 0)
        latest = logs[0]
        self.assertIn("safety_score", latest)
        self.assertIn("risk_level", latest)


if __name__ == "__main__":
    unittest.main()
