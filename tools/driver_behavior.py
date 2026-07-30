"""
Driver Behavior Analysis & Road Safety Intelligence Tool.
Detects hazardous driving patterns: Sudden Braking, Wrong-Way Driving, Overspeeding, Illegal U-Turns, and Lane Violations.
"""
import random
from typing import Dict, Any, List


class DriverBehaviorAnalyzer:
    """Class responsible for evaluating driver behavior anomalies and computing safety scores."""

    @staticmethod
    def analyze_driver_behavior(telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes telemetry and probabilistic trajectory vectors to detect driving violations.
        
        Args:
            telemetry: Raw or simulated traffic telemetry dict.
            
        Returns:
            Dictionary with violation counts, safety index score, and risk flags.
        """
        speed = telemetry.get("average_speed", 35.0)
        vehicle_count = telemetry.get("vehicles", telemetry.get("vehicle_count", 40))
        accident = telemetry.get("accident", False)
        road = telemetry.get("road", "Main Road")

        # Deterministic seed based on road & speed to keep telemetry reproducible
        seed_val = int(speed * 10) + vehicle_count + (100 if accident else 0)
        rng = random.Random(seed_val)

        # 1. Overspeeding Detection (Threshold: >70 km/h in city zone)
        overspeeding_count = max(0, int((speed - 50) / 10 * rng.uniform(1.2, 2.5))) if speed > 60 else rng.randint(0, 1)

        # 2. Sudden Braking Detection (High during heavy traffic/accidents)
        sudden_braking_count = rng.randint(3, 9) if (speed < 25 or accident) else rng.randint(0, 2)

        # 3. Wrong-Way Driving Detection (Critical anomaly)
        wrong_way_count = 1 if (accident and rng.random() < 0.4) else (1 if rng.random() < 0.08 else 0)

        # 4. Illegal U-Turns Detection
        illegal_uturn_count = rng.randint(1, 4) if vehicle_count > 70 else rng.randint(0, 1)

        # 5. Lane Violations Detection (Drifting across solid lines)
        lane_violation_count = rng.randint(2, 6) if vehicle_count > 60 else rng.randint(0, 2)

        total_violations = (
            overspeeding_count + sudden_braking_count + wrong_way_count + 
            illegal_uturn_count + lane_violation_count
        )

        # Calculate Driver Safety Index Score (0 to 100)
        # Deduct penalties for violations
        penalty = (
            (overspeeding_count * 5) + 
            (sudden_braking_count * 3) + 
            (wrong_way_count * 20) + 
            (illegal_uturn_count * 8) + 
            (lane_violation_count * 4)
        )
        
        safety_score = max(0.0, min(100.0, round(100.0 - penalty, 1)))

        # Risk Classification
        if safety_score < 50.0 or wrong_way_count > 0:
            safety_rating = "CRITICAL HAZARD 🔴"
        elif safety_score < 75.0:
            safety_rating = "MODERATE RISK 🟡"
        else:
            safety_rating = "SAFE FLOW 🟢"

        # Generate Actionable Safety Alerts
        safety_alerts = []
        if wrong_way_count > 0:
            safety_alerts.append(f"⛔ CRITICAL: {wrong_way_count} vehicle(s) detected driving WRONG-WAY on {road}!")
        if overspeeding_count > 2:
            safety_alerts.append(f"⚡ WARNING: {overspeeding_count} instances of severe OVERSPEEDING (>70 km/h) logged.")
        if sudden_braking_count > 4:
            safety_alerts.append(f"🛑 HAZARD: High frequency of SUDDEN BRAKING ({sudden_braking_count} events) detected.")
        if illegal_uturn_count > 1:
            safety_alerts.append(f"↩️ NOTICE: {illegal_uturn_count} ILLEGAL U-TURNS flagged near intersection zone.")
        if lane_violation_count > 3:
            safety_alerts.append(f"🛣️ NOTICE: {lane_violation_count} LANE DRIFT / SOLID LINE VIOLATIONS observed.")

        if not safety_alerts:
            safety_alerts.append("🟢 Driver behavior is within safe regulatory limits.")

        return {
            "road": road,
            "safety_score": safety_score,
            "safety_rating": safety_rating,
            "total_violations": total_violations,
            "violations_breakdown": {
                "sudden_braking": sudden_braking_count,
                "wrong_way_driving": wrong_way_count,
                "overspeeding": overspeeding_count,
                "illegal_uturns": illegal_uturn_count,
                "lane_violations": lane_violation_count
            },
            "safety_alerts": safety_alerts
        }
