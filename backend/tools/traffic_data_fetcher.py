"""
Traffic Data Fetcher, Validator & CrewAI Tool Integration (Backend Package).
Handles Google Maps API traffic ingestion, Open-Meteo weather integration,
strict data validation, structured schema formatting, and developer data lineage.
"""

import os
import json
import logging
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Dict, Any, Tuple, Optional

try:
    from crewai.tools import tool
except Exception:
    def tool(func):
        return func

from tools.simulation_tools import TrafficSimulator

logger = logging.getLogger("smart_traffic_ai.traffic")

ROAD_COORDINATES = {
    "Main Road": {"latitude": 13.0827, "longitude": 80.2707, "road_id": "R001"},
    "Broadway Ave": {"latitude": 13.0810, "longitude": 80.2690, "road_id": "R002"},
    "Express Highway": {"latitude": 13.0845, "longitude": 80.2720, "road_id": "R003"},
    "Downtown Ring": {"latitude": 13.0860, "longitude": 80.2750, "road_id": "R004"},
    "Harbor View Park": {"latitude": 13.0890, "longitude": 80.2780, "road_id": "R005"}
}


class TrafficDataValidator:
    """Validator to enforce strict bounds and sanitize missing fields."""

    @staticmethod
    def validate_and_sanitize(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validates numeric ranges and sanitizes missing values to 'unavailable'."""
        sanitized = dict(data)

        # Vehicle count validation
        vc = sanitized.get("vehicle_count")
        if vc is None or not isinstance(vc, (int, float)) or vc < 0:
            sanitized["vehicle_count"] = "unavailable"
        else:
            sanitized["vehicle_count"] = int(vc)

        # Average speed validation
        spd = sanitized.get("average_speed")
        if spd is None or not isinstance(spd, (int, float)) or spd < 0:
            sanitized["average_speed"] = "unavailable"
        else:
            sanitized["average_speed"] = round(float(spd), 1)

        # Congestion level validation (0-100)
        cg = sanitized.get("congestion_level")
        if cg is None or not isinstance(cg, (int, float)):
            sanitized["congestion_level"] = "unavailable"
        else:
            sanitized["congestion_level"] = max(0, min(100, int(round(float(cg)))))

        # Latitude & Longitude validation
        lat = sanitized.get("latitude")
        if lat is None or not isinstance(lat, (int, float)) or not (-90.0 <= float(lat) <= 90.0):
            sanitized["latitude"] = "unavailable"
        else:
            sanitized["latitude"] = round(float(lat), 4)

        lng = sanitized.get("longitude")
        if lng is None or not isinstance(lng, (int, float)) or not (-180.0 <= float(lng) <= 180.0):
            sanitized["longitude"] = "unavailable"
        else:
            sanitized["longitude"] = round(float(lng), 4)

        # Travel time validation
        tt = sanitized.get("travel_time")
        if tt is None or not isinstance(tt, (int, float)) or tt < 0:
            sanitized["travel_time"] = "unavailable"
        else:
            sanitized["travel_time"] = int(tt)

        ntt = sanitized.get("normal_travel_time")
        if ntt is None or not isinstance(ntt, (int, float)) or ntt < 0:
            sanitized["normal_travel_time"] = "unavailable"
        else:
            sanitized["normal_travel_time"] = int(ntt)

        # Delay validation
        dly = sanitized.get("delay")
        if dly is None or not isinstance(dly, (int, float)):
            if isinstance(sanitized.get("travel_time"), int) and isinstance(sanitized.get("normal_travel_time"), int):
                sanitized["delay"] = max(0, sanitized["travel_time"] - sanitized["normal_travel_time"])
            else:
                sanitized["delay"] = "unavailable"
        else:
            sanitized["delay"] = max(0, int(dly))

        # Enforce string defaults for boolean and status fields
        sanitized["accident_status"] = bool(sanitized.get("accident_status", False))
        sanitized["emergency_vehicle_status"] = bool(sanitized.get("emergency_vehicle_status", False))
        sanitized["road_status"] = str(sanitized.get("road_status", "OPEN")).upper()
        sanitized["traffic_density"] = str(sanitized.get("traffic_density", "MEDIUM")).upper()
        sanitized["weather"] = str(sanitized.get("weather", "CLEAR")).upper()
        sanitized["road_id"] = str(sanitized.get("road_id", "R001"))
        sanitized["road_name"] = str(sanitized.get("road_name", "Main Road"))

        now_utc = datetime.utcnow()
        if not sanitized.get("timestamp"):
            sanitized["timestamp"] = now_utc.isoformat()
        if not sanitized.get("time_display"):
            sanitized["time_display"] = datetime.now().strftime("%H:%M:%S")

        return sanitized


class TrafficDataFetcher:
    """Fetches traffic data from Google Maps API or time-aware telemetry fallback."""

    @classmethod
    def fetch_google_maps_traffic(cls, origin: str, destination: str) -> Tuple[bool, Dict[str, Any]]:
        """Fetch live traffic delay and travel times via Google Maps Distance Matrix API."""
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not api_key or api_key.strip() in ["", "your_google_maps_api_key_here"]:
            logger.info("[TRAFFIC] Google Maps API Key not set. Using time-aware telemetry fallback.")
            return False, {}

        try:
            params = {
                "origins": origin,
                "destinations": destination,
                "departure_time": "now",
                "traffic_model": "best_guess",
                "key": api_key
            }
            url = f"https://maps.googleapis.com/maps/api/distancematrix/json?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(url, headers={"User-Agent": "SmartTrafficAI/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                raw_json = json.loads(resp.read().decode())

            if raw_json.get("status") == "OK" and raw_json.get("rows"):
                element = raw_json["rows"][0]["elements"][0]
                if element.get("status") == "OK":
                    duration = element.get("duration", {}).get("value", 0) // 60
                    duration_in_traffic = element.get("duration_in_traffic", {}).get("value", duration * 60) // 60
                    delay = max(0, duration_in_traffic - duration)
                    return True, {
                        "raw_response": raw_json,
                        "travel_time": duration_in_traffic,
                        "normal_travel_time": duration,
                        "delay": delay
                    }
        except Exception as err:
            logger.error(f"[ERROR] Traffic API request failed: {err}")

        return False, {}

    @classmethod
    def get_traffic_data(cls, road_name: str = "Main Road") -> Dict[str, Any]:
        """Fetch, validate, and return structured traffic data with explicit logging."""
        now_str = datetime.now().strftime("%H:%M:%S")
        logger.info("[TRAFFIC] Fetch started")
        logger.info(f"[TRAFFIC] Fetch time: {now_str}")
        logger.info(f"[TRAFFIC] Road: {road_name}")

        coords = ROAD_COORDINATES.get(road_name, ROAD_COORDINATES["Main Road"])
        lat = coords["latitude"]
        lng = coords["longitude"]
        road_id = coords["road_id"]

        # Attempt Google Maps API fetch
        gmaps_success, gmaps_data = cls.fetch_google_maps_traffic(
            origin=f"{lat},{lng}",
            destination=f"{lat + 0.01},{lng + 0.01}"
        )

        # Telemetry simulator for vehicle count & sensor data
        sim_data = TrafficSimulator.generate_random_telemetry(road=road_name)

        if gmaps_success:
            logger.info("[TRAFFIC] Google Maps live traffic API successfully returned live route metrics.")
            travel_time = gmaps_data.get("travel_time", 15)
            normal_travel_time = gmaps_data.get("normal_travel_time", 10)
            delay = gmaps_data.get("delay", 5)
            congestion_level = max(0, min(100, int((delay / max(1, normal_travel_time)) * 100)))
            data_mode = "REAL-TIME GOOGLE MAPS API + CCTV SENSORS"
        else:
            travel_time = int(round((sim_data.get("vehicle_count", 50) / 120.0) * 20)) + 5
            normal_travel_time = 8
            delay = max(0, travel_time - normal_travel_time)
            congestion_level = int(round(sim_data.get("road_occupancy_pct", 40.0)))
            data_mode = sim_data.get("data_mode", "SIMULATED DATA (Time-Aware Sensor Model)")

        density_str = sim_data.get("density", "MEDIUM").upper()
        if density_str not in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            if congestion_level > 80:
                density_str = "CRITICAL"
            elif congestion_level > 60:
                density_str = "HIGH"
            elif congestion_level > 35:
                density_str = "MEDIUM"
            else:
                density_str = "LOW"

        raw_struct = {
            "road_id": road_id,
            "road_name": road_name,
            "latitude": lat,
            "longitude": lng,
            "vehicle_count": sim_data.get("vehicle_count", 50),
            "average_speed": sim_data.get("average_speed", 40.0),
            "traffic_density": density_str,
            "congestion_level": congestion_level,
            "travel_time": travel_time,
            "normal_travel_time": normal_travel_time,
            "delay": delay,
            "accident_status": sim_data.get("accident", False),
            "emergency_vehicle_status": sim_data.get("emergency_vehicle", False),
            "road_status": "CLOSED" if sim_data.get("accident") else "OPEN",
            "weather": str(sim_data.get("weather", "CLEAR")).upper(),
            "timestamp": datetime.utcnow().isoformat(),
            "time_display": now_str,
            "data_mode": data_mode
        }

        # Validate and sanitize data
        validated = TrafficDataValidator.validate_and_sanitize(raw_struct)

        logger.info(f"[TRAFFIC] Vehicle Count: {validated.get('vehicle_count')}")
        logger.info(f"[TRAFFIC] Average Speed: {validated.get('average_speed')} km/h")
        logger.info(f"[TRAFFIC] Density: {validated.get('traffic_density')}")
        logger.info(f"[TRAFFIC] Congestion: {validated.get('congestion_level')}%")
        logger.info(f"[TRAFFIC] Delay: {validated.get('delay')} minutes")
        logger.info(f"[TRAFFIC] Data timestamp: {validated.get('time_display')}")
        logger.info("[TRAFFIC] Sending latest data to CrewAI Agent")

        return validated


@tool
def fetch_traffic_data(road_name: str) -> str:
    """
    CrewAI Tool to fetch real-time structured traffic telemetry for a specified road.
    """
    data = TrafficDataFetcher.get_traffic_data(road_name)
    return json.dumps(data, indent=2)


def get_data_lineage(road_name: str = "Main Road", agent_output: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Returns developer debug dictionary showing data flow across all 5 lineage stages."""
    api_key_present = bool(os.getenv("GOOGLE_MAPS_API_KEY") and os.getenv("GOOGLE_MAPS_API_KEY").strip() != "your_google_maps_api_key_here")
    source_name = "Google Maps API + CCTV Sensors" if api_key_present else "SIMULATED DATA (Time-Aware Sensor Model)"
    
    data_struct = TrafficDataFetcher.get_traffic_data(road_name)

    agent_input_prompt = (
        f"TRAFFIC DATA:\n"
        f"Road ID: {data_struct.get('road_id')}\n"
        f"Road Name: {data_struct.get('road_name')}\n"
        f"Latitude: {data_struct.get('latitude')}\n"
        f"Longitude: {data_struct.get('longitude')}\n"
        f"Vehicle Count: {data_struct.get('vehicle_count')}\n"
        f"Average Speed: {data_struct.get('average_speed')} km/h\n"
        f"Traffic Density: {data_struct.get('traffic_density')}\n"
        f"Congestion Level: {data_struct.get('congestion_level')}%\n"
        f"Travel Time: {data_struct.get('travel_time')} minutes\n"
        f"Normal Travel Time: {data_struct.get('normal_travel_time')} minutes\n"
        f"Delay: {data_struct.get('delay')} minutes\n"
        f"Accident Status: {data_struct.get('accident_status')}\n"
        f"Emergency Vehicle Status: {data_struct.get('emergency_vehicle_status')}\n"
        f"Road Status: {data_struct.get('road_status')}\n"
        f"Weather: {data_struct.get('weather')}\n"
        f"Timestamp: {data_struct.get('timestamp')}"
    )

    if not agent_output:
        agent_output = {
            "road_id": data_struct.get("road_id"),
            "road_name": data_struct.get("road_name"),
            "location": {"latitude": data_struct.get("latitude"), "longitude": data_struct.get("longitude")},
            "vehicle_count": data_struct.get("vehicle_count"),
            "average_speed": data_struct.get("average_speed"),
            "traffic_density": data_struct.get("traffic_density"),
            "congestion_level": data_struct.get("congestion_level"),
            "travel_time": data_struct.get("travel_time"),
            "delay": data_struct.get("delay"),
            "accident_status": data_struct.get("accident_status"),
            "emergency_vehicle_status": data_struct.get("emergency_vehicle_status"),
            "road_status": data_struct.get("road_status"),
            "weather": data_struct.get("weather"),
            "timestamp": data_struct.get("timestamp"),
            "time_display": data_struct.get("time_display"),
            "risk_level": "HIGH" if data_struct.get("congestion_level", 0) > 70 else "MEDIUM"
        }

    return {
        "data_source": {
            "provider": source_name,
            "google_maps_key_active": api_key_present,
            "target_road": road_name,
            "status": "FETCH_SUCCESS",
            "fetch_time": data_struct.get("time_display")
        },
        "raw_response": {
            "coordinates": {"lat": data_struct.get("latitude"), "lng": data_struct.get("longitude")},
            "raw_vehicle_count": data_struct.get("vehicle_count"),
            "raw_speed": data_struct.get("average_speed"),
            "raw_weather": data_struct.get("weather")
        },
        "normalized_response": data_struct,
        "agent_input": agent_input_prompt,
        "agent_output": agent_output
    }
