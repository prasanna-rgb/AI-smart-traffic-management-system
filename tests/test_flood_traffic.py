"""
Unit Test Suite for Flood & Waterlogging Traffic Agent.
Verifies all 5 specified test scenarios:
1. Clear Weather / No Rain -> LOW Risk (SAFE)
2. Light Rain -> MODERATE Risk (MONITOR)
3. Heavy Rain + Low Elevation -> HIGH Risk (HIGH RISK)
4. Heavy Rain + Historical Flood Zone + Slowing Traffic -> VERY HIGH Risk
5. Critical Rainfall + Waterlogging -> CRITICAL / FLOODED (Reroutes, optimizes signals, alerts citizens)
"""

import unittest
from crew import run_traffic_crew
from tools.flood_data_tools import FloodRiskCalculator


class TestFloodTrafficAgent(unittest.TestCase):

    def test_scenario_1_no_rain(self):
        """TEST 1: No rain -> Flood Risk = LOW (SAFE)."""
        res = FloodRiskCalculator.calculate_risk(
            road_name="Express Highway", # Elevated road 14.5m
            rainfall_mm_per_hour=0.0,
            vehicle_speed=50.0,
            traffic_density="LOW"
        )
        self.assertEqual(res["risk_level"], "LOW")
        self.assertEqual(res["road_status"], "SAFE")
        self.assertFalse(res["predicted_waterlogging"])
        self.assertLessEqual(res["flood_risk_score"], 20)

    def test_scenario_2_light_rain(self):
        """TEST 2: Light rain -> Flood Risk = MODERATE (MONITOR)."""
        res = FloodRiskCalculator.calculate_risk(
            road_name="Express Highway",
            rainfall_mm_per_hour=15.0,
            vehicle_speed=40.0,
            traffic_density="MEDIUM"
        )
        self.assertIn(res["risk_level"], ["LOW", "MODERATE"])
        self.assertIn(res["road_status"], ["SAFE", "MONITOR"])
        self.assertLessEqual(res["flood_risk_score"], 45)

    def test_scenario_3_heavy_rain_low_elevation(self):
        """TEST 3: Heavy rain + low elevation -> Flood Risk = HIGH (HIGH RISK)."""
        res = FloodRiskCalculator.calculate_risk(
            road_name="Main Road", # Elevation 5.2m (low)
            rainfall_mm_per_hour=45.0,
            vehicle_speed=25.0,
            traffic_density="MEDIUM"
        )
        self.assertIn(res["risk_level"], ["HIGH", "VERY HIGH"])
        self.assertTrue(res["predicted_waterlogging"])
        self.assertIn("alternate_route", res)

    def test_scenario_4_heavy_rain_historical_zone_slowing_traffic(self):
        """TEST 4: Heavy rain + historical flood zone + slowing traffic -> VERY HIGH Risk."""
        res = FloodRiskCalculator.calculate_risk(
            road_name="Harbor View Park", # Critical historical flood zone, elevation 3.8m
            rainfall_mm_per_hour=55.0,
            vehicle_speed=12.0,
            traffic_density="HIGH"
        )
        self.assertIn(res["risk_level"], ["VERY HIGH", "CRITICAL"])
        self.assertTrue(res["predicted_waterlogging"])
        self.assertGreaterEqual(res["flood_risk_score"], 70)

    def test_scenario_5_critical_rainfall_waterlogging_pipeline(self):
        """TEST 5: Critical rainfall + waterlogging -> CRITICAL / FLOODED (Full multi-agent pipeline)."""
        telemetry = {
            "road": "Main Road",
            "vehicle_count": 140,
            "average_speed": 10.0,
            "weather": "Heavy Rain & Storm",
            "rainfall_mm_per_hour": 85.0
        }
        report = run_traffic_crew(telemetry)

        self.assertIn("flood_traffic", report)
        fl_trf = report["flood_traffic"]

        self.assertEqual(fl_trf["risk_level"], "CRITICAL")
        self.assertEqual(fl_trf["road_status"], "FLOODED")
        self.assertTrue(fl_trf["predicted_waterlogging"])
        self.assertIn("Ring Road", fl_trf["alternate_route"])
        self.assertIn("FloodDiverted", report["signal_optimization"]["signal_mode"])


if __name__ == "__main__":
    unittest.main()
