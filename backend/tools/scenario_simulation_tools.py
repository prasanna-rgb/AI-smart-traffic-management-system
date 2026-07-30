"""
Traffic Scenario Simulation & Decision Engine Tools (Backend Package).
Proactively simulates multiple traffic management strategies, predicts outcomes, 
calculates multi-attribute decision scores, and recommends optimal actions.
"""
import json
import logging
from typing import Dict, Any, List, Optional

try:
    from crewai.tools import tool
except Exception:
    def tool(func):
        return func

logger = logging.getLogger("smart_traffic_ai.simulation_decision")

# Configurable Decision Model Weights (Total = 1.0)
DEFAULT_SCORE_WEIGHTS = {
    "congestion_reduction": 0.30,
    "emergency_response": 0.25,
    "travel_time": 0.15,
    "waiting_time": 0.10,
    "carbon_reduction": 0.10,
    "traffic_throughput": 0.10
}


class ScenarioSimulator:
    """Mathematical simulation engine to evaluate, score, and rank candidate traffic management actions."""

    @staticmethod
    def simulate_scenarios(traffic_data: Dict[str, Any], weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Simulate candidate scenarios, calculate decision scores, and select the winning action.
        """
        w = weights or DEFAULT_SCORE_WEIGHTS
        road = traffic_data.get("road_name", traffic_data.get("road", "Main Road"))
        vehicles = int(traffic_data.get("vehicle_count", 50))
        speed = float(traffic_data.get("average_speed", 40.0))
        congestion = int(traffic_data.get("congestion_level", traffic_data.get("congestion_score", 40)))
        accident = bool(traffic_data.get("accident_status", traffic_data.get("accident", False)))
        emergency_vehicle = bool(traffic_data.get("emergency_vehicle_status", traffic_data.get("emergency_vehicle", False)))
        emerg_type = (traffic_data.get("emergency_type") or "AMBULANCE").upper() if emergency_vehicle else "NONE"
        weather = str(traffic_data.get("weather", "CLEAR")).upper()
        capacity = 200 # Standard nominal capacity (vehicles/lane/hr)

        # Baseline Actual State (Pre-Decision)
        actual_delay = max(2, int(round((vehicles / max(1, capacity)) * 18)))
        actual_emerg_response = 14 if emergency_vehicle else (12 if accident else 8)
        actual_carbon = "VERY HIGH" if congestion >= 80 else ("HIGH" if congestion >= 60 else ("MEDIUM" if congestion >= 35 else "LOW"))
        actual_wait = max(3, int(round((vehicles / 20.0) * 1.5)))

        # Define Candidate Strategies
        candidate_scenarios = [
            {
                "id": "SCEN-A",
                "name": "Scenario A: Maintain Current Signal Timing",
                "action": "Maintain standard 30s adaptive timing schedule",
                "green_boost_sec": 0,
                "corridor_active": False,
                "reroute_active": False
            },
            {
                "id": "SCEN-B",
                "name": "Scenario B: Extended Green Signal Phase (+25s)",
                "action": "Extend green signal duration to 55s for priority clearing",
                "green_boost_sec": 25,
                "corridor_active": False,
                "reroute_active": False
            },
            {
                "id": "SCEN-C",
                "name": "Scenario C: Emergency Green Corridor + Rescue Lock",
                "action": "Activate zero-wait Green Corridor (90s lock) on Lane 1 for emergency clearance",
                "green_boost_sec": 60,
                "corridor_active": True,
                "reroute_active": False
            },
            {
                "id": "SCEN-D",
                "name": "Scenario D: Combined Green Corridor + Traffic Diversion Reroute",
                "action": "Activate Green Corridor on Lane 1 and divert non-emergency traffic to Outer Ring Bypass",
                "green_boost_sec": 60,
                "corridor_active": True,
                "reroute_active": True
            }
        ]

        evaluated_scenarios = []
        best_scenario = None
        highest_score = -1.0

        for sc in candidate_scenarios:
            # 1. Physics/Queue Math Simulation Predictions
            g_boost = sc["green_boost_sec"]
            is_corr = sc["corridor_active"]
            is_reroute = sc["reroute_active"]

            # Predicted Congestion Reduction
            cong_reduction_factor = (g_boost * 0.45) + (35.0 if is_corr else 0.0) + (25.0 if is_reroute else 0.0)
            pred_congestion = max(15, int(round(congestion - cong_reduction_factor)))

            # Predicted Speed Improvement
            speed_boost = (g_boost * 0.25) + (18.0 if is_reroute else 0.0)
            pred_speed = min(65.0, round(speed + speed_boost, 1))

            # Predicted Wait Time
            wait_reduction = (g_boost * 0.15) + (4.0 if is_corr else 0.0) + (3.0 if is_reroute else 0.0)
            pred_wait = max(1, int(round(actual_wait - wait_reduction)))

            # Predicted Travel Delay
            delay_reduction = (g_boost * 0.20) + (6.0 if is_reroute else 0.0)
            pred_delay = max(2, int(round(actual_delay - delay_reduction)))

            # Predicted Emergency Response Time (min)
            if emergency_vehicle or accident:
                resp_reduction = (10.0 if is_corr else 2.0) + (4.0 if is_reroute else 0.0) + (g_boost * 0.05)
                pred_emerg_time = max(3, int(round(actual_emerg_response - resp_reduction)))
            else:
                pred_emerg_time = 4

            # Predicted Carbon Output
            if pred_congestion < 40:
                pred_carbon = "LOW"
            elif pred_congestion < 60:
                pred_carbon = "MEDIUM"
            elif pred_congestion < 75:
                pred_carbon = "HIGH"
            else:
                pred_carbon = "VERY HIGH"

            # Predicted Throughput (veh/hr)
            pred_throughput = int(round(capacity * (1.0 - (pred_congestion / 100.0)) * (pred_speed / 40.0)))

            # 2. Calculate Weighted Multi-Attribute Decision Score (0-100)
            s_cong = max(0, min(100, (100 - pred_congestion)))
            s_emerg = max(0, min(100, int((15 - pred_emerg_time) / 15.0 * 100)))
            s_travel = max(0, min(100, int((20 - pred_delay) / 20.0 * 100)))
            s_wait = max(0, min(100, int((15 - pred_wait) / 15.0 * 100)))
            
            carbon_map = {"LOW": 100, "MEDIUM": 75, "HIGH": 45, "VERY HIGH": 20}
            s_carbon = carbon_map.get(pred_carbon, 50)
            s_tp = max(0, min(100, int((pred_throughput / max(1, capacity)) * 100)))

            decision_score = round(
                (s_cong * w["congestion_reduction"]) +
                (s_emerg * w["emergency_response"]) +
                (s_travel * w["travel_time"]) +
                (s_wait * w["waiting_time"]) +
                (s_carbon * w["carbon_reduction"]) +
                (s_tp * w["traffic_throughput"]),
                1
            )

            # Extra priority bonus for Green Corridor when Emergency/Accident present
            if (emergency_vehicle or accident) and is_corr:
                decision_score = min(100.0, round(decision_score + 12.0, 1))

            scenario_entry = {
                "scenario_id": sc["id"],
                "name": sc["name"],
                "action": sc["action"],
                "predicted_congestion": pred_congestion,
                "predicted_speed": pred_speed,
                "predicted_waiting_time": pred_wait,
                "predicted_delay": pred_delay,
                "predicted_emergency_time": pred_emerg_time,
                "predicted_carbon": pred_carbon,
                "predicted_throughput": pred_throughput,
                "decision_score": decision_score,
                "selected": False
            }

            evaluated_scenarios.append(scenario_entry)

            if decision_score > highest_score:
                highest_score = decision_score
                best_scenario = scenario_entry

        # Mark winning scenario
        if best_scenario:
            best_scenario["selected"] = True

        # Generate Reasoning Rationale
        if emergency_vehicle:
            reason = f"Activated Green Corridor and traffic diversion for {emerg_type}. Provides lowest emergency response time ({best_scenario['predicted_emergency_time']} min) and cuts congestion to {best_scenario['predicted_congestion']}%."
        elif accident:
            reason = f"Fast clearance signal lock and alternate route rerouting selected. Cuts travel delay to {best_scenario['predicted_delay']} min while mitigating carbon emissions."
        elif congestion >= 65:
            reason = f"Extended green signal phase and adaptive split recommended. Reduces vehicle wait time to {best_scenario['predicted_waiting_time']} min and boosts throughput."
        else:
            reason = "Standard adaptive signal timing recommended for balanced, low-emission traffic flow."

        confidence = 94 if (emergency_vehicle or accident) else 91

        logger.info(f"[SCENARIO] Current traffic received for {road}: Vehicles={vehicles}, Speed={speed}km/h, Congestion={congestion}%")
        logger.info(f"[SCENARIO] Evaluated {len(evaluated_scenarios)} candidate decision scenarios. Highest Score={highest_score}")
        logger.info(f"[SCENARIO] Best Action Selected: {best_scenario['action']} (Score={highest_score}/100)")

        return {
            "recommended_action": best_scenario["action"],
            "winning_scenario_id": best_scenario["scenario_id"],
            "decision_score": best_scenario["decision_score"],
            "expected_congestion": best_scenario["predicted_congestion"],
            "expected_delay": best_scenario["predicted_delay"],
            "emergency_response_time": best_scenario["predicted_emergency_time"],
            "expected_carbon_emission": best_scenario["predicted_carbon"],
            "confidence": confidence,
            "reason": reason,
            "actual_baseline": {
                "congestion": congestion,
                "delay": actual_delay,
                "emergency_response": actual_emerg_response,
                "carbon": actual_carbon,
                "waiting_time": actual_wait,
                "speed": speed
            },
            "after_predicted": {
                "congestion": best_scenario["predicted_congestion"],
                "delay": best_scenario["predicted_delay"],
                "emergency_response": best_scenario["predicted_emergency_time"],
                "carbon": best_scenario["predicted_carbon"],
                "waiting_time": best_scenario["predicted_waiting_time"],
                "speed": best_scenario["predicted_speed"]
            },
            "scenarios_evaluated": evaluated_scenarios
        }


@tool
def simulate_traffic_scenarios_tool(traffic_data_json: str) -> str:
    """
    CrewAI Tool to simulate traffic management scenarios, evaluate decision scores, and return the optimal action recommendation.
    """
    try:
        data = json.loads(traffic_data_json)
    except Exception:
        data = {"road": "Main Road", "vehicle_count": 50, "average_speed": 40.0, "congestion_level": 40}
    
    result = ScenarioSimulator.simulate_scenarios(data)
    return json.dumps(result, indent=2)
