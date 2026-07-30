"""
Traffic Telemetry Simulation Tools.
Simulates CCTV / IoT sensor stream with realistic random distributions.
"""
import random
from typing import Dict, Any

ROADS = ["Main Road", "Broadway Ave", "Express Highway", "Downtown Ring", "Harbor View Park"]
WEATHER_OPTIONS = ["Clear", "Clear", "Rain", "Fog", "Storm"]
EMERGENCY_TYPES = ["Ambulance", "Fire Truck", "Police Vehicle"]


class TrafficSimulator:
    """Class responsible for generating synthetic real-time traffic telemetry."""

    @staticmethod
    def generate_random_telemetry(road: str = None) -> Dict[str, Any]:
        """Generate probabilistic real-time traffic data."""
        target_road = road if road else random.choice(ROADS)
        
        # Determine scenario (Peak Hour, Accident, Emergency, Normal)
        scenario_roll = random.random()
        
        if scenario_roll < 0.15: # Emergency Scenario
            vehicle_count = random.randint(70, 110)
            avg_speed = random.randint(15, 30)
            occupancy = round(random.uniform(75.0, 95.0), 1)
            accident = False
            emergency_vehicle = True
            emergency_type = random.choice(EMERGENCY_TYPES)
        elif scenario_roll < 0.30: # Accident Scenario
            vehicle_count = random.randint(80, 120)
            avg_speed = random.randint(10, 20)
            occupancy = round(random.uniform(85.0, 98.0), 1)
            accident = True
            emergency_vehicle = random.choice([True, False])
            emergency_type = "Ambulance" if emergency_vehicle else None
        elif scenario_roll < 0.65: # Heavy Traffic
            vehicle_count = random.randint(65, 95)
            avg_speed = random.randint(25, 40)
            occupancy = round(random.uniform(60.0, 80.0), 1)
            accident = False
            emergency_vehicle = False
            emergency_type = None
        else: # Normal / Light Traffic
            vehicle_count = random.randint(20, 55)
            avg_speed = random.randint(45, 65)
            occupancy = round(random.uniform(25.0, 55.0), 1)
            accident = False
            emergency_vehicle = False
            emergency_type = None

        weather = random.choice(WEATHER_OPTIONS)

        return {
            "road": target_road,
            "vehicle_count": vehicle_count,
            "average_speed": avg_speed,
            "road_occupancy_pct": occupancy,
            "accident": accident,
            "emergency_vehicle": emergency_vehicle,
            "emergency_type": emergency_type,
            "weather": weather
        }
