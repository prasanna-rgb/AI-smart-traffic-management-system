"""
SUMO (Simulation of Urban MObility) Integration Bridge & Camera Simulation Connector.
"""
import requests
import logging
from typing import Dict, Any

logger = logging.getLogger("smart_traffic_ai.tools.sumo")

class SUMOBridge:
    """Connector class for bridging SUMO simulation software or Traci server with CrewAI backend."""

    def __init__(self, backend_url: str = "http://127.0.0.1:8000"):
        self.backend_url = backend_url

    def send_sumo_step(self, intersection_code: str, vehicle_count: int, avg_speed_m_s: float, has_emergency: bool) -> Dict[str, Any]:
        """Post step telemetry from SUMO simulation to FastAPI backend."""
        endpoint = f"{self.backend_url}/api/traffic/sumo/sync"
        payload = {
            "intersection_code": intersection_code,
            "vehicle_count": vehicle_count,
            "avg_speed_m_s": avg_speed_m_s,
            "has_emergency_vehicle": has_emergency
        }
        try:
            response = requests.post(endpoint, json=payload, timeout=5)
            return response.json()
        except Exception as e:
            logger.error(f"Failed to post SUMO step to backend: {e}")
            return {"error": str(e)}
