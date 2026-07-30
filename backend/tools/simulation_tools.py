"""
Traffic Telemetry Simulation Tools (Backend Package).
Simulates realistic, time-of-day aware CCTV / IoT sensor telemetry with continuous dynamic variations.
Includes high-reliability emergency vehicle & accident event triggers.
"""
import random
from datetime import datetime
from typing import Dict, Any

ROADS = ["Main Road", "Broadway Ave", "Express Highway", "Downtown Ring", "Harbor View Park"]
WEATHER_OPTIONS = ["Clear", "Clear", "Rain", "Fog", "Storm"]
EMERGENCY_TYPES = ["Ambulance", "Fire Truck", "Police Vehicle"]

# Global in-memory cache for stateful gradual transitions between fetch cycles
_PREVIOUS_ROAD_STATES: Dict[str, Dict[str, Any]] = {}


class TrafficSimulator:
    """Class responsible for generating synthetic real-time traffic telemetry with state continuity."""

    @staticmethod
    def generate_random_telemetry(road: str = None) -> Dict[str, Any]:
        """Generate time-aware dynamic real-time traffic data with active emergency vehicle triggers."""
        target_road = road if road else random.choice(ROADS)
        now = datetime.now()
        hour = now.hour

        # Determine base time-of-day profile
        if 7 <= hour <= 9:  # Morning Peak
            base_vc = random.randint(140, 185)
            base_speed = random.uniform(18.0, 28.0)
            base_occupancy = random.uniform(75.0, 92.0)
            density_desc = "HIGH"
        elif 17 <= hour <= 20:  # Evening Peak
            base_vc = random.randint(160, 215)
            base_speed = random.uniform(14.0, 24.0)
            base_occupancy = random.uniform(82.0, 96.0)
            density_desc = "CRITICAL"
        elif 10 <= hour <= 16:  # Mid-day Normal
            base_vc = random.randint(65, 115)
            base_speed = random.uniform(35.0, 52.0)
            base_occupancy = random.uniform(42.0, 68.0)
            density_desc = "MEDIUM"
        else:  # Night Light Traffic
            base_vc = random.randint(20, 55)
            base_speed = random.uniform(50.0, 68.0)
            base_occupancy = random.uniform(15.0, 38.0)
            density_desc = "LOW"

        # Apply stateful smooth variation relative to previous fetch cycle if available
        prev_state = _PREVIOUS_ROAD_STATES.get(target_road)
        if prev_state:
            vc_delta = random.randint(-12, 16)
            vehicle_count = max(10, prev_state.get("vehicle_count", base_vc) + vc_delta)

            speed_delta = round(random.uniform(-3.5, 3.5), 1)
            avg_speed = max(10.0, round(prev_state.get("average_speed", base_speed) + speed_delta, 1))

            occ_delta = round(random.uniform(-4.0, 4.0), 1)
            occupancy = max(10.0, min(99.0, round(prev_state.get("road_occupancy_pct", base_occupancy) + occ_delta, 1)))
        else:
            vehicle_count = base_vc
            avg_speed = round(base_speed, 1)
            occupancy = round(base_occupancy, 1)

        # Active Dynamic Emergency & Accident Triggers (45% total event probability)
        event_roll = random.random()
        if event_roll < 0.20:
            accident = True
            emergency_vehicle = True
            emergency_type = random.choice(EMERGENCY_TYPES)
            vehicle_count += random.randint(20, 40)
            avg_speed = max(8.0, avg_speed - 14.0)
            occupancy = min(98.0, occupancy + 20.0)
            density_desc = "CRITICAL"
        elif event_roll < 0.45:
            accident = False
            emergency_vehicle = True
            emergency_type = random.choice(EMERGENCY_TYPES)
        else:
            accident = False
            emergency_vehicle = False
            emergency_type = None

        weather = random.choice(WEATHER_OPTIONS)
        timestamp_str = datetime.utcnow().isoformat()
        time_display = now.strftime("%H:%M:%S")

        result = {
            "road": target_road,
            "vehicle_count": vehicle_count,
            "average_speed": avg_speed,
            "road_occupancy_pct": occupancy,
            "density": density_desc,
            "accident": accident,
            "emergency_vehicle": emergency_vehicle,
            "emergency_type": emergency_type,
            "weather": weather,
            "timestamp": timestamp_str,
            "time_display": time_display,
            "data_mode": "SIMULATED DATA (Time-Aware Sensor Model)"
        }

        # Cache state for next fetch cycle transition
        _PREVIOUS_ROAD_STATES[target_road] = result
        return result
