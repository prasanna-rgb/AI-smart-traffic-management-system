"""
Tools and Algorithms for Emergency Resource Allocation Agent (Backend Package).
Retrieves available fleet ambulances and nearby hospitals, evaluates multi-attribute suitability scores,
calculates total ETAs via Google Maps API (Ambulance -> Accident -> Hospital), and provides AI allocation recommendations.
"""

import math
import uuid
import json
import os
import urllib.parse
import urllib.request
from typing import Dict, Any, List, Optional
try:
    from crewai.tools import tool
except Exception:
    def tool(func):
        return func

from database.db import save_emergency_allocation


class AmbulanceRegistry:
    """Mock/Simulated Ambulance Fleet Registry Tool."""

    AMBULANCE_FLEET = [
        {
            "ambulance_id": "AMB001",
            "latitude": 13.0750,
            "longitude": 80.2600,
            "status": "AVAILABLE",
            "ambulance_type": "Advanced Life Support",
            "medical_equipment": "Defibrillator, Ventilator, Monitor",
            "oxygen_available": True,
            "ICU_support": True,
            "paramedic_available": True,
            "current_destination": "Base Station 1"
        },
        {
            "ambulance_id": "AMB002",
            "latitude": 13.0890,
            "longitude": 80.2780,
            "status": "AVAILABLE",
            "ambulance_type": "Basic Life Support",
            "medical_equipment": "First Aid, Oxygen, Stretcher",
            "oxygen_available": True,
            "ICU_support": False,
            "paramedic_available": True,
            "current_destination": "Base Station 2"
        },
        {
            "ambulance_id": "AMB003",
            "latitude": 13.0950,
            "longitude": 80.2850,
            "status": "AVAILABLE",
            "ambulance_type": "Advanced Life Support",
            "medical_equipment": "Advanced Cardiac Care, Ventilator",
            "oxygen_available": True,
            "ICU_support": True,
            "paramedic_available": True,
            "current_destination": "Base Station 3"
        },
        {
            "ambulance_id": "AMB004",
            "latitude": 13.0700,
            "longitude": 80.2500,
            "status": "BUSY",
            "ambulance_type": "Critical Care Transport",
            "medical_equipment": "Full ICU Rig",
            "oxygen_available": True,
            "ICU_support": True,
            "paramedic_available": True,
            "current_destination": "Transfer Patient"
        }
    ]

    @classmethod
    def get_available_ambulances(cls) -> List[Dict[str, Any]]:
        """Retrieve only AVAILABLE fleet ambulances."""
        return [amb for amb in cls.AMBULANCE_FLEET if amb.get("status") == "AVAILABLE"]


class HospitalRegistry:
    """Mock/Simulated Hospital Regional Registry Tool."""

    HOSPITAL_NETWORK = [
        {
            "hospital_id": "H001",
            "hospital_name": "City Emergency Hospital",
            "latitude": 13.0670,
            "longitude": 80.2550,
            "emergency_available": True,
            "ICU_available": True,
            "trauma_center": True,
            "beds_available": 8,
            "ventilator_available": 3,
            "ambulance_receiving_status": "ACCEPTING"
        },
        {
            "hospital_id": "H002",
            "hospital_name": "Metro Trauma Center",
            "latitude": 13.0900,
            "longitude": 80.2800,
            "emergency_available": True,
            "ICU_available": True,
            "trauma_center": True,
            "beds_available": 14,
            "ventilator_available": 6,
            "ambulance_receiving_status": "ACCEPTING"
        },
        {
            "hospital_id": "H003",
            "hospital_name": "St. Jude Memorial Hospital",
            "latitude": 13.0800,
            "longitude": 80.2650,
            "emergency_available": True,
            "ICU_available": False,
            "trauma_center": True,
            "beds_available": 4,
            "ventilator_available": 1,
            "ambulance_receiving_status": "ACCEPTING"
        },
        {
            "hospital_id": "H004",
            "hospital_name": "Suburb Medical Clinic",
            "latitude": 13.1100,
            "longitude": 80.3000,
            "emergency_available": False,
            "ICU_available": False,
            "trauma_center": False,
            "beds_available": 0,
            "ventilator_available": 0,
            "ambulance_receiving_status": "DIVERTED"
        }
    ]

    @classmethod
    def get_nearby_hospitals(cls) -> List[Dict[str, Any]]:
        """Retrieve hospitals accepting emergency ambulances."""
        return [h for h in cls.HOSPITAL_NETWORK if h.get("ambulance_receiving_status") == "ACCEPTING"]


class EmergencyResourceScorer:
    """Configurable multi-attribute decision scoring engine for emergency resources."""

    DEFAULT_AMBULANCE_WEIGHTS = {
        "travel_time": 0.35,
        "capability": 0.25,
        "traffic": 0.20,
        "distance": 0.10,
        "availability": 0.10
    }

    DEFAULT_HOSPITAL_WEIGHTS = {
        "emergency": 0.25,
        "icu": 0.25,
        "trauma": 0.20,
        "travel_time": 0.20,
        "distance": 0.10
    }

    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate approximate distance in kilometers between coordinates."""
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(R * c, 2)

    @staticmethod
    def fetch_google_maps_route(origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float) -> Dict[str, Any]:
        """Fetch live Google Maps Distance Matrix travel time and construct navigation URLs."""
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        nav_url = f"https://www.google.com/maps/dir/?api=1&origin={origin_lat},{origin_lon}&destination={dest_lat},{dest_lon}&travelmode=driving"
        embed_url = f"https://maps.google.com/maps?q={dest_lat},{dest_lon}&t=&z=14&ie=UTF8&iwloc=&output=embed"

        if not api_key or api_key.strip() in ["", "your_google_maps_api_key_here"]:
            return {
                "google_maps_active": False,
                "google_maps_nav_url": nav_url,
                "google_maps_embed_url": embed_url,
                "travel_time_minutes": None,
                "distance_km": None
            }

        try:
            params = {
                "origins": f"{origin_lat},{origin_lon}",
                "destinations": f"{dest_lat},{dest_lon}",
                "departure_time": "now",
                "traffic_model": "best_guess",
                "key": api_key
            }
            url = f"https://maps.googleapis.com/maps/api/distancematrix/json?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(url, headers={"User-Agent": "SmartTrafficAI-Emergency/1.0"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode())
                if data.get("status") == "OK" and data.get("rows"):
                    elem = data["rows"][0]["elements"][0]
                    if elem.get("status") == "OK":
                        dist_km = round(elem.get("distance", {}).get("value", 0) / 1000.0, 2)
                        dur_traffic_min = max(1, elem.get("duration_in_traffic", {}).get("value", elem.get("duration", {}).get("value", 0)) // 60)
                        return {
                            "google_maps_active": True,
                            "google_maps_nav_url": nav_url,
                            "google_maps_embed_url": embed_url,
                            "travel_time_minutes": dur_traffic_min,
                            "distance_km": dist_km
                        }
        except Exception:
            pass

        return {
            "google_maps_active": False,
            "google_maps_nav_url": nav_url,
            "google_maps_embed_url": embed_url,
            "travel_time_minutes": None,
            "distance_km": None
        }

    @classmethod
    def score_ambulance(cls, ambulance: Dict[str, Any], accident: Dict[str, Any], weights: Dict[str, float] = None) -> Dict[str, Any]:
        """Score candidate ambulance based on ETA, medical capability, traffic, distance, and availability."""
        w = weights or cls.DEFAULT_AMBULANCE_WEIGHTS
        acc_lat = accident.get("latitude", 13.0827)
        acc_lon = accident.get("longitude", 80.2707)
        acc_severity = str(accident.get("severity", accident.get("accident_severity", "MEDIUM"))).upper()
        traffic_density = str(accident.get("traffic_density", "MEDIUM")).upper()

        gmaps_info = cls.fetch_google_maps_route(ambulance["latitude"], ambulance["longitude"], acc_lat, acc_lon)
        if gmaps_info.get("google_maps_active") and gmaps_info.get("travel_time_minutes"):
            eta_minutes = gmaps_info["travel_time_minutes"]
            dist_km = gmaps_info["distance_km"]
        else:
            dist_km = cls.calculate_distance(ambulance["latitude"], ambulance["longitude"], acc_lat, acc_lon)
            if dist_km < 0.2:
                dist_km = 0.5
            speed_kmh = 45.0 if traffic_density == "MEDIUM" else (30.0 if traffic_density == "HIGH" else 60.0)
            eta_minutes = max(2, int(round((dist_km / speed_kmh) * 60)))

        s_eta = max(0, min(100, int((15 - eta_minutes) / 15 * 100)))
        
        is_als = "ADVANCED" in ambulance.get("ambulance_type", "").upper()
        has_icu = ambulance.get("ICU_support", False)
        if acc_severity in ["CRITICAL", "HIGH"]:
            s_cap = 100 if (is_als and has_icu) else (70 if is_als else 40)
        else:
            s_cap = 100 if is_als else 85

        s_traffic = 90 if traffic_density == "LOW" else (70 if traffic_density == "MEDIUM" else 45)
        s_dist = max(0, min(100, int((10 - dist_km) / 10 * 100)))
        s_avail = 100 if ambulance.get("status") == "AVAILABLE" else 0

        final_score = round(
            (w["travel_time"] * s_eta) +
            (w["capability"] * s_cap) +
            (w["traffic"] * s_traffic) +
            (w["distance"] * s_dist) +
            (w["availability"] * s_avail),
            1
        )

        return {
            "ambulance_id": ambulance["ambulance_id"],
            "ambulance_type": ambulance["ambulance_type"],
            "distance_km": dist_km,
            "eta_minutes": eta_minutes,
            "traffic_density": traffic_density,
            "capability_rating": "HIGH" if s_cap >= 90 else ("MEDIUM" if s_cap >= 60 else "LOW"),
            "score": final_score,
            "google_maps_nav_url": gmaps_info["google_maps_nav_url"]
        }

    @classmethod
    def score_hospital(cls, hospital: Dict[str, Any], accident: Dict[str, Any], weights: Dict[str, float] = None) -> Dict[str, Any]:
        """Score candidate hospital based on Emergency Dept, ICU beds, Trauma Center status, ETA, and distance."""
        w = weights or cls.DEFAULT_HOSPITAL_WEIGHTS
        acc_lat = accident.get("latitude", 13.0827)
        acc_lon = accident.get("longitude", 80.2707)
        acc_severity = str(accident.get("severity", accident.get("accident_severity", "MEDIUM"))).upper()
        traffic_density = str(accident.get("traffic_density", "MEDIUM")).upper()

        gmaps_info = cls.fetch_google_maps_route(acc_lat, acc_lon, hospital["latitude"], hospital["longitude"])
        if gmaps_info.get("google_maps_active") and gmaps_info.get("travel_time_minutes"):
            eta_minutes = gmaps_info["travel_time_minutes"]
            dist_km = gmaps_info["distance_km"]
        else:
            dist_km = cls.calculate_distance(hospital["latitude"], hospital["longitude"], acc_lat, acc_lon)
            if dist_km < 0.2:
                dist_km = 0.5
            speed_kmh = 40.0 if traffic_density in ["HIGH", "CRITICAL"] else 55.0
            eta_minutes = max(3, int(round((dist_km / speed_kmh) * 60)))

        s_emerg = 100 if hospital.get("emergency_available", False) else 0
        has_icu = hospital.get("ICU_available", False) and hospital.get("beds_available", 0) > 0
        s_icu = 100 if has_icu else 30
        has_trauma = hospital.get("trauma_center", False)
        s_trauma = 100 if has_trauma else 40
        s_eta = max(0, min(100, int((20 - eta_minutes) / 20 * 100)))
        s_dist = max(0, min(100, int((15 - dist_km) / 15 * 100)))

        priority_bonus = 0.0
        if acc_severity in ["CRITICAL", "HIGH"] and has_icu and has_trauma:
            priority_bonus = 10.0

        final_score = round(
            min(100.0, (w["emergency"] * s_emerg) +
            (w["icu"] * s_icu) +
            (w["trauma"] * s_trauma) +
            (w["travel_time"] * s_eta) +
            (w["distance"] * s_dist) + priority_bonus),
            1
        )

        return {
            "hospital_id": hospital["hospital_id"],
            "hospital_name": hospital["hospital_name"],
            "latitude": hospital["latitude"],
            "longitude": hospital["longitude"],
            "distance_km": dist_km,
            "travel_time_minutes": eta_minutes,
            "icu_available": hospital.get("ICU_available", False),
            "trauma_center": hospital.get("trauma_center", False),
            "beds_available": hospital.get("beds_available", 0),
            "score": final_score,
            "google_maps_nav_url": gmaps_info["google_maps_nav_url"],
            "google_maps_embed_url": gmaps_info["google_maps_embed_url"],
            "google_maps_active": gmaps_info["google_maps_active"]
        }


class ResourceAllocatorEngine:
    """Main execution engine for Emergency Resource Allocation."""

    @classmethod
    def allocate_resources(cls, accident_data: Dict[str, Any], amb_unavailable: List[str] = None, hosp_unavailable: List[str] = None) -> Dict[str, Any]:
        """
        Evaluate candidate ambulances and hospitals, score options, select optimal pairing, and format output.
        """
        accident_id = accident_data.get("accident_id", f"ACC-{uuid.uuid4().hex[:4].upper()}")
        road_name = accident_data.get("road_name", accident_data.get("road", "Main Road"))
        severity = str(accident_data.get("severity", accident_data.get("accident_severity", "CRITICAL"))).upper()
        traffic = str(accident_data.get("traffic_density", "HIGH")).upper()
        acc_lat = accident_data.get("latitude", 13.0827)
        acc_lon = accident_data.get("longitude", 80.2707)

        amb_unavail = amb_unavailable or []
        hosp_unavail = hosp_unavailable or []

        ambulances = [a for a in AmbulanceRegistry.get_available_ambulances() if a["ambulance_id"] not in amb_unavail]
        if not ambulances:
            ambulances = AmbulanceRegistry.AMBULANCE_FLEET[:1]

        hospitals = [h for h in HospitalRegistry.get_nearby_hospitals() if h["hospital_id"] not in hosp_unavail]
        if not hospitals:
            hospitals = HospitalRegistry.HOSPITAL_NETWORK[:1]

        scored_ambulances = []
        for amb in ambulances:
            sc = EmergencyResourceScorer.score_ambulance(amb, accident_data)
            scored_ambulances.append(sc)

        scored_ambulances.sort(key=lambda x: x["score"], reverse=True)
        best_amb = scored_ambulances[0]

        scored_hospitals = []
        for hosp in hospitals:
            sc = EmergencyResourceScorer.score_hospital(hosp, accident_data)
            scored_hospitals.append(sc)

        scored_hospitals.sort(key=lambda x: x["score"], reverse=True)
        best_hosp = scored_hospitals[0]

        total_response_time = best_amb["eta_minutes"] + best_hosp["travel_time_minutes"]
        overall_score = round((best_amb["score"] * 0.5) + (best_hosp["score"] * 0.5), 1)

        recommended_route = f"{road_name} → Outer Ring Expressway → {best_hosp['hospital_name']}"

        gmaps_nav_url = best_hosp.get("google_maps_nav_url", f"https://www.google.com/maps/dir/?api=1&origin={acc_lat},{acc_lon}&destination={best_hosp.get('latitude', 13.0900)},{best_hosp.get('longitude', 80.2800)}&travelmode=driving")
        gmaps_embed_url = best_hosp.get("google_maps_embed_url", f"https://maps.google.com/maps?q={best_hosp.get('latitude', 13.0900)},{best_hosp.get('longitude', 80.2800)}&t=&z=14&ie=UTF8&iwloc=&output=embed")
        gmaps_active = best_hosp.get("google_maps_active", False)

        reason = (
            f"Ambulance {best_amb['ambulance_id']} was selected because it provides the best balance between "
            f"response time ({best_amb['eta_minutes']} min), traffic conditions ({traffic}), and {best_amb['capability_rating']} medical capability. "
            f"Hospital {best_hosp['hospital_name']} was selected as the optimal nearest facility with ICU & trauma-care capability "
            f"and a travel time of {best_hosp['travel_time_minutes']} min via Google Maps routing."
        )

        res = {
            "allocation_id": f"ALLOC-{uuid.uuid4().hex[:6].upper()}",
            "accident_id": accident_id,
            "accident_location": road_name,
            "accident_severity": severity,
            "traffic_conditions": traffic,

            "selected_ambulance": {
                "ambulance_id": best_amb["ambulance_id"],
                "response_time_minutes": best_amb["eta_minutes"],
                "capability": best_amb["ambulance_type"].upper(),
                "distance_km": best_amb["distance_km"],
                "score": best_amb["score"]
            },

            "selected_hospital": {
                "hospital_id": best_hosp["hospital_id"],
                "hospital_name": best_hosp["hospital_name"],
                "travel_time_minutes": best_hosp["travel_time_minutes"],
                "icu_available": best_hosp["icu_available"],
                "trauma_center": best_hosp["trauma_center"],
                "beds_available": best_hosp["beds_available"],
                "latitude": best_hosp.get("latitude", 13.0900),
                "longitude": best_hosp.get("longitude", 80.2800),
                "google_maps_nav_url": gmaps_nav_url,
                "google_maps_embed_url": gmaps_embed_url,
                "google_maps_active": gmaps_active,
                "score": best_hosp["score"]
            },

            "total_estimated_time": total_response_time,
            "recommended_route": recommended_route,
            "google_maps_nav_url": gmaps_nav_url,
            "google_maps_embed_url": gmaps_embed_url,
            "google_maps_api_active": gmaps_active,
            "decision_score": overall_score,
            "reason": reason,

            "ambulance_options": scored_ambulances,
            "hospital_options": scored_hospitals,

            "green_corridor_status": "REQUESTED_ACTIVE",
            "allocation_status": "EN_ROUTE_ACCIDENT",
            "is_simulated": True,
            "disclaimer": "Recommended Emergency Resource Allocation - Final dispatch and hospital decisions remain with authorized emergency personnel."
        }

        try:
            save_emergency_allocation(res)
        except Exception:
            pass

        return res


@tool
def allocate_emergency_resources_tool(accident_id: str, road_name: str, severity: str, estimated_injuries: int = 2) -> str:
    """
    Intelligently allocates the optimal available ambulance and hospital for a traffic accident.
    Calculates multi-attribute suitability scores, ETAs, and optimal emergency routes.
    """
    acc_payload = {
        "accident_id": accident_id,
        "road_name": road_name,
        "severity": severity,
        "estimated_injuries": estimated_injuries,
        "latitude": 13.0827,
        "longitude": 80.2707,
        "traffic_density": "HIGH"
    }
    alloc_res = ResourceAllocatorEngine.allocate_resources(acc_payload)
    return (
        f"🚨 EMERGENCY RESOURCE ALLOCATION RESULT\n"
        f"Selected Ambulance: {alloc_res['selected_ambulance']['ambulance_id']} ({alloc_res['selected_ambulance']['capability']}, ETA: {alloc_res['selected_ambulance']['response_time_minutes']} min)\n"
        f"Selected Hospital: {alloc_res['selected_hospital']['hospital_name']} (Travel Time: {alloc_res['selected_hospital']['travel_time_minutes']} min, ICU: {alloc_res['selected_hospital']['icu_available']})\n"
        f"Total Emergency Response Time: {alloc_res['total_estimated_time']} minutes\n"
        f"Decision Score: {alloc_res['decision_score']}/100\n"
        f"Recommended Route: {alloc_res['recommended_route']}\n"
        f"Reason: {alloc_res['reason']}"
    )
