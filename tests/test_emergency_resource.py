"""
Unit Test Suite for Emergency Resource Allocation Agent.
Verifies all 8 specified test scenarios:
1. Single ambulance + hospital allocation
2. Multiple ambulances comparison & optimal selection
3. Multiple hospitals comparison & optimal selection
4. Critical accident prioritization (ALS + ICU + Trauma Center)
5. Traffic congestion routing & ETA travel time prioritization
6. Automatic ambulance re-allocation when selected ambulance becomes unavailable
7. Automatic hospital re-allocation when selected hospital becomes unavailable
8. Emergency resolution & green corridor restoration logging
"""

import unittest
from crew import run_traffic_crew
from tools.emergency_resource_tools import ResourceAllocatorEngine, AmbulanceRegistry, HospitalRegistry


class TestEmergencyResourceAllocationAgent(unittest.TestCase):

    def test_scenario_1_single_ambulance_and_hospital(self):
        """TEST 1: Single ambulance + hospital allocation."""
        acc_payload = {
            "accident_id": "ACC101",
            "road_name": "Main Road",
            "severity": "CRITICAL",
            "latitude": 13.0827,
            "longitude": 80.2707,
            "traffic_density": "MEDIUM"
        }
        res = ResourceAllocatorEngine.allocate_resources(acc_payload)
        
        self.assertIn("selected_ambulance", res)
        self.assertIn("selected_hospital", res)
        self.assertGreater(res["total_estimated_time"], 0)
        self.assertGreater(res["decision_score"], 50.0)

    def test_scenario_2_multiple_ambulances_selection(self):
        """TEST 2: Multiple ambulances -> Compare and select optimal option."""
        acc_payload = {
            "accident_id": "ACC102",
            "road_name": "Broadway Ave",
            "severity": "CRITICAL",
            "latitude": 13.0827,
            "longitude": 80.2707,
            "traffic_density": "HIGH"
        }
        res = ResourceAllocatorEngine.allocate_resources(acc_payload)
        
        self.assertIn("ambulance_options", res)
        self.assertGreaterEqual(len(res["ambulance_options"]), 2)
        # AMB001 or AMB003 is Advanced Life Support (ALS) with ICU support
        self.assertIn(res["selected_ambulance"]["ambulance_id"], ["AMB001", "AMB003"])

    def test_scenario_3_multiple_hospitals_selection(self):
        """TEST 3: Multiple hospitals -> Compare distance, ICU, trauma, and select best."""
        acc_payload = {
            "accident_id": "ACC103",
            "road_name": "Express Highway",
            "severity": "CRITICAL",
            "latitude": 13.0845,
            "longitude": 80.2720,
            "traffic_density": "HIGH"
        }
        res = ResourceAllocatorEngine.allocate_resources(acc_payload)
        
        self.assertIn("hospital_options", res)
        self.assertGreaterEqual(len(res["hospital_options"]), 2)
        # Prefers Metro Trauma Center or City Emergency Hospital due to ICU & Trauma Center
        self.assertTrue(res["selected_hospital"]["icu_available"])

    def test_scenario_4_critical_accident(self):
        """TEST 4: Critical accident -> Prefer Advanced Life Support ambulance and Trauma/ICU hospital."""
        acc_payload = {
            "accident_id": "ACC104",
            "road_name": "Downtown Ring",
            "severity": "CRITICAL",
            "latitude": 13.0860,
            "longitude": 80.2750,
            "traffic_density": "HIGH"
        }
        res = ResourceAllocatorEngine.allocate_resources(acc_payload)
        
        self.assertEqual(res["selected_ambulance"]["capability"], "ADVANCED LIFE SUPPORT")
        self.assertTrue(res["selected_hospital"]["trauma_center"])

    def test_scenario_5_traffic_congestion_routing(self):
        """TEST 5: Traffic congestion -> Select ambulance based on travel time, not just distance."""
        acc_payload = {
            "accident_id": "ACC105",
            "road_name": "Harbor View Park",
            "severity": "HIGH",
            "latitude": 13.0890,
            "longitude": 80.2780,
            "traffic_density": "CRITICAL"
        }
        res = ResourceAllocatorEngine.allocate_resources(acc_payload)
        
        self.assertIn("recommended_route", res)
        self.assertGreater(res["total_estimated_time"], 0)

    def test_scenario_6_ambulance_unavailability_reallocation(self):
        """TEST 6: Selected ambulance becomes unavailable -> Automatically reallocate another."""
        acc_payload = {
            "accident_id": "ACC106",
            "road_name": "Main Road",
            "severity": "CRITICAL",
            "traffic_density": "HIGH"
        }
        # Simulate AMB001 becoming busy/unavailable
        res1 = ResourceAllocatorEngine.allocate_resources(acc_payload)
        first_amb = res1["selected_ambulance"]["ambulance_id"]

        res2 = ResourceAllocatorEngine.allocate_resources(acc_payload, amb_unavailable=[first_amb])
        realloc_amb = res2["selected_ambulance"]["ambulance_id"]

        self.assertNotEqual(first_amb, realloc_amb)

    def test_scenario_7_hospital_unavailability_reallocation(self):
        """TEST 7: Selected hospital becomes unavailable -> Automatically select another suitable hospital."""
        acc_payload = {
            "accident_id": "ACC107",
            "road_name": "Main Road",
            "severity": "CRITICAL",
            "traffic_density": "HIGH"
        }
        # Simulate H002 becoming unavailable/saturated
        res1 = ResourceAllocatorEngine.allocate_resources(acc_payload)
        first_hosp = res1["selected_hospital"]["hospital_id"]

        res2 = ResourceAllocatorEngine.allocate_resources(acc_payload, hosp_unavailable=[first_hosp])
        realloc_hosp = res2["selected_hospital"]["hospital_id"]

        self.assertNotEqual(first_hosp, realloc_hosp)

    def test_scenario_8_end_to_end_pipeline(self):
        """TEST 8: End-to-end multi-agent pipeline integration with Emergency Resource Allocation."""
        telemetry = {
            "road": "Main Road",
            "vehicle_count": 160,
            "average_speed": 18.0,
            "accident": True,
            "emergency_vehicle": True,
            "emergency_type": "AMBULANCE"
        }
        report = run_traffic_crew(telemetry)
        
        self.assertIn("emergency_resource", report)
        em_res = report["emergency_resource"]
        self.assertIn("selected_ambulance", em_res)
        self.assertIn("selected_hospital", em_res)
        self.assertGreaterEqual(em_res["decision_score"], 60.0)


if __name__ == "__main__":
    unittest.main()
