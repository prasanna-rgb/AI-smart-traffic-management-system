"""
Driver Behavior Analysis & Safety Analytics Tools.
Provides violation detection routines, Driver Safety Score calculation (0-100),
Risk Level classification, Driver Risk Prediction, and Location Intelligence.
"""

from typing import Dict, Any, List


class DriverBehaviorTools:
    """Class containing detection logic, scoring, and safety intelligence for vehicle telemetry."""

    # Default configurable penalty weights
    DEFAULT_WEIGHTS = {
        "wrong_way": 35,
        "extreme_overspeeding": 25,
        "overspeeding": 15,
        "illegal_u_turn": 15,
        "dangerous_lane_change": 12,
        "sudden_braking": 10,
        "lane_violations": 8,
        "repeated_violation_multiplier": 1.2
    }

    @classmethod
    def evaluate_telemetry(cls, telemetry: Dict[str, Any], weights: Dict[str, int] = None) -> Dict[str, Any]:
        """
        Main entry point to analyze vehicle telemetry and return structured safety analytics.
        
        Args:
            telemetry: Telemetry payload dict.
            weights: Optional custom penalty weights dictionary.
            
        Returns:
            Structured JSON report matching project specification.
        """
        w = weights or cls.DEFAULT_WEIGHTS

        # Extract telemetry fields with sensible defaults
        vehicle_id = telemetry.get("vehicle_id", telemetry.get("vehicle", "VH101"))
        speed = float(telemetry.get("speed", telemetry.get("average_speed", 45.0)))
        speed_limit = float(telemetry.get("speed_limit", 60.0))
        acceleration = float(telemetry.get("acceleration", 0.0))
        braking_intensity = float(telemetry.get("braking_intensity", 0.0))
        current_lane = telemetry.get("current_lane", 1)
        previous_lane = telemetry.get("previous_lane", 1)
        lane_change = telemetry.get("lane_change", current_lane != previous_lane)
        wrong_way = telemetry.get("wrong_way", False) or telemetry.get("driving_direction") == "WRONG_WAY"
        u_turn = telemetry.get("u_turn", False) or telemetry.get("illegal_u_turn", False)
        
        # Location intelligence coordinates
        loc = telemetry.get("location", telemetry.get("gps_location", {}))
        if not loc or not isinstance(loc, dict):
            loc = {"latitude": 13.0827, "longitude": 80.2707}
        latitude = float(loc.get("latitude", loc.get("lat", 13.0827)))
        longitude = float(loc.get("longitude", loc.get("lng", 80.2707)))
        road_id = telemetry.get("road_id", telemetry.get("road", "Main Road"))

        # Explicit violation counters (passed directly or detected from real-time parameters)
        raw_violations = telemetry.get("violations", {})
        
        # 1. Sudden Braking
        sudden_braking_count = raw_violations.get("sudden_braking", 0)
        if sudden_braking_count == 0 and (acceleration < -5.0 or braking_intensity > 0.7):
            sudden_braking_count = int(abs(acceleration) / 2.0) if acceleration < -5.0 else 1

        # 2. Overspeeding
        overspeeding_count = raw_violations.get("overspeeding", 0)
        is_extreme_speed = speed > (speed_limit + 20)
        if overspeeding_count == 0 and speed > speed_limit:
            overspeeding_count = 1

        # 3. Wrong-Way Driving
        wrong_way_count = raw_violations.get("wrong_way", 1 if wrong_way else 0)

        # 4. Illegal U-Turn
        illegal_uturn_count = raw_violations.get("illegal_u_turn", 1 if u_turn else 0)

        # 5. Lane Violations
        lane_violations_count = raw_violations.get("lane_violations", 1 if (lane_change and (speed > speed_limit or sudden_braking_count > 0)) else 0)

        # 6. Total Violations Count
        total_violations = (
            sudden_braking_count + wrong_way_count + overspeeding_count +
            illegal_uturn_count + lane_violations_count
        )

        # Calculate Driver Safety Score (0 - 100)
        penalty = 0.0
        penalty += wrong_way_count * w.get("wrong_way", 35)
        if is_extreme_speed:
            penalty += overspeeding_count * w.get("extreme_overspeeding", 25)
        else:
            penalty += overspeeding_count * w.get("overspeeding", 15)
        penalty += sudden_braking_count * w.get("sudden_braking", 10)
        penalty += illegal_uturn_count * w.get("illegal_u_turn", 15)
        penalty += lane_violations_count * w.get("lane_violations", 8)

        # Apply multiplier for repeated violations (>5 total violations)
        if total_violations > 5:
            penalty *= w.get("repeated_violation_multiplier", 1.2)

        safety_score = max(0, min(100, int(round(100.0 - penalty))))

        # Determine Risk Level & Classification
        if safety_score <= 39 or wrong_way_count > 0:
            risk_level = "CRITICAL"
        elif safety_score <= 59:
            risk_level = "HIGH"
        elif safety_score <= 79:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Determine Primary Hazard
        primary_hazard = "None"
        if wrong_way_count > 0:
            primary_hazard = "Wrong-way driving detected"
        elif sudden_braking_count >= 4:
            primary_hazard = "Frequent sudden braking"
        elif is_extreme_speed:
            primary_hazard = "Extreme overspeeding"
        elif overspeeding_count > 0:
            primary_hazard = "Overspeeding limit breach"
        elif illegal_uturn_count > 0:
            primary_hazard = "Unauthorized U-turn in restricted zone"
        elif lane_violations_count > 0:
            primary_hazard = "Unsafe lane drift across solid line"
        elif total_violations > 0:
            primary_hazard = "Multiple driving infractions"

        # Formulate Actionable Recommendation
        if risk_level == "CRITICAL":
            recommendation = "Immediate driver safety warning required & dispatch traffic enforcement unit"
        elif risk_level == "HIGH":
            recommendation = "Issue high-priority driver warning and flag vehicle for close monitoring"
        elif risk_level == "MEDIUM":
            recommendation = "Send gentle speed & lane advisory notice to driver"
        else:
            recommendation = "Maintain safe driving behavior"

        # Driver Risk Prediction Engine
        if total_violations >= 5 or wrong_way_count > 0 or sudden_braking_count >= 4:
            pred_prob = "HIGH"
            pred_statement = f"Driver has a {pred_prob} probability of future unsafe driving."
            pred_action = "Trigger automated safety alert to driver dashboard & log profile in high-risk registry."
        elif total_violations >= 2:
            pred_prob = "MODERATE"
            pred_statement = f"Driver has a {pred_prob} probability of future unsafe driving."
            pred_action = "Display speed limit & distance awareness prompt."
        else:
            pred_prob = "LOW"
            pred_statement = "Driver maintains LOW probability of future unsafe driving."
            pred_action = "No intervention required."

        # Safety Intelligence Alert Text
        alert_headline = primary_hazard.upper()
        alert_text = (
            f"🚨 SAFETY INTELLIGENCE ALERT\n\n"
            f"Vehicle: {vehicle_id}\n\n"
            f"{alert_headline}\n\n"
            f"{total_violations} total violation event(s) detected.\n\n"
            f"Safety Score: {safety_score}/100\n\n"
            f"Risk Level: {risk_level}\n\n"
            f"Recommended Action:\n{recommendation}"
        )

        return {
            "vehicle_id": vehicle_id,
            "safety_score": safety_score,
            "risk_level": risk_level,
            "violations": {
                "sudden_braking": sudden_braking_count,
                "wrong_way": wrong_way_count,
                "overspeeding": overspeeding_count,
                "illegal_u_turn": illegal_uturn_count,
                "lane_violations": lane_violations_count
            },
            "total_violations": total_violations,
            "location": {
                "latitude": latitude,
                "longitude": longitude
            },
            "road_id": road_id,
            "primary_hazard": primary_hazard,
            "recommendation": recommendation,
            "risk_prediction": {
                "probability": pred_prob,
                "statement": pred_statement,
                "preventive_action": pred_action
            },
            "location_intelligence": {
                "road_id": road_id,
                "latitude": latitude,
                "longitude": longitude,
                "zone_classification": "Accident-Prone Zone" if total_violations > 3 else "Standard Corridor"
            },
            "formatted_alert": alert_text
        }

    @classmethod
    def get_test_cases(cls) -> List[Dict[str, Any]]:
        """Returns 6 predefined telemetry test cases for demonstration and testing."""
        return [
            {
                "case_name": "1. Safe Driver",
                "telemetry": {
                    "vehicle_id": "VH101",
                    "speed": 50,
                    "speed_limit": 60,
                    "acceleration": -0.5,
                    "braking_intensity": 0.1,
                    "lane_change": False,
                    "wrong_way": False,
                    "u_turn": False,
                    "road_id": "Main Road",
                    "location": {"latitude": 13.0827, "longitude": 80.2707}
                }
            },
            {
                "case_name": "2. Overspeeding Driver",
                "telemetry": {
                    "vehicle_id": "VH102",
                    "speed": 95,
                    "speed_limit": 60,
                    "acceleration": 2.1,
                    "braking_intensity": 0.2,
                    "lane_change": False,
                    "wrong_way": False,
                    "u_turn": False,
                    "road_id": "Express Highway",
                    "location": {"latitude": 13.0845, "longitude": 80.2720}
                }
            },
            {
                "case_name": "3. Frequent Sudden Braking",
                "telemetry": {
                    "vehicle_id": "VH103",
                    "speed": 45,
                    "speed_limit": 60,
                    "acceleration": -8.5,
                    "braking_intensity": 0.9,
                    "violations": {
                        "sudden_braking": 6,
                        "wrong_way": 0,
                        "overspeeding": 0,
                        "illegal_u_turn": 0,
                        "lane_violations": 0
                    },
                    "road_id": "Broadway Ave",
                    "location": {"latitude": 13.0810, "longitude": 80.2690}
                }
            },
            {
                "case_name": "4. Wrong-Way Driver",
                "telemetry": {
                    "vehicle_id": "VH104",
                    "speed": 55,
                    "speed_limit": 60,
                    "wrong_way": True,
                    "driving_direction": "WRONG_WAY",
                    "violations": {
                        "sudden_braking": 1,
                        "wrong_way": 1,
                        "overspeeding": 0,
                        "illegal_u_turn": 0,
                        "lane_violations": 1
                    },
                    "road_id": "Downtown Ring",
                    "location": {"latitude": 13.0860, "longitude": 80.2750}
                }
            },
            {
                "case_name": "5. Multiple Violations",
                "telemetry": {
                    "vehicle_id": "VH105",
                    "speed": 92,
                    "speed_limit": 60,
                    "acceleration": -8.5,
                    "lane_change": True,
                    "wrong_way": False,
                    "u_turn": True,
                    "violations": {
                        "sudden_braking": 6,
                        "wrong_way": 0,
                        "overspeeding": 1,
                        "illegal_u_turn": 4,
                        "lane_violations": 2
                    },
                    "road_id": "Main Road",
                    "location": {"latitude": 13.0827, "longitude": 80.2707}
                }
            },
            {
                "case_name": "6. Critical-Risk Driver",
                "telemetry": {
                    "vehicle_id": "VH106",
                    "speed": 110,
                    "speed_limit": 60,
                    "wrong_way": True,
                    "acceleration": -9.2,
                    "violations": {
                        "sudden_braking": 5,
                        "wrong_way": 1,
                        "overspeeding": 1,
                        "illegal_u_turn": 3,
                        "lane_violations": 3
                    },
                    "road_id": "Harbor View Park",
                    "location": {"latitude": 13.0890, "longitude": 80.2780}
                }
            }
        ]
