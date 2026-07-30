"""
SQLAlchemy ORM Models for Database Tables.
"""
from datetime import datetime
import json
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class IntersectionDB(Base):
    """Intersection Metadata & Real-time Signal State."""
    __tablename__ = "intersections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True) # e.g. INT-01
    name = Column(String(150), nullable=False)
    location_lat = Column(Float, default=37.7749)
    location_lng = Column(Float, default=-122.4194)
    total_lanes = Column(Integer, default=4)
    signal_mode = Column(String(50), default="AI_AUTO") # AI_AUTO, MANUAL, EMERGENCY_CORRIDOR
    active_phase = Column(String(50), default="NORTH_SOUTH_GREEN")
    ns_green_timer = Column(Integer, default=30)
    ew_green_timer = Column(Integer, default=30)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "lat": self.location_lat,
            "lng": self.location_lng,
            "total_lanes": self.total_lanes,
            "signal_mode": self.signal_mode,
            "active_phase": self.active_phase,
            "ns_green_timer": self.ns_green_timer,
            "ew_green_timer": self.ew_green_timer,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class VisionMetricDB(Base):
    """Raw & Aggregated YOLOv8 Detection Telemetry per Frame Batch."""
    __tablename__ = "vision_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    intersection_code = Column(String(50), nullable=False, index=True)
    car_count = Column(Integer, default=0)
    bus_count = Column(Integer, default=0)
    truck_count = Column(Integer, default=0)
    motorcycle_count = Column(Integer, default=0)
    ambulance_count = Column(Integer, default=0)
    total_vehicles = Column(Integer, default=0)
    average_speed = Column(Float, default=40.0)
    density_pct = Column(Float, default=0.0)
    detections_json = Column(Text, nullable=True) # Serialized list of detection boxes

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "intersection_code": self.intersection_code,
            "car": self.car_count,
            "bus": self.bus_count,
            "truck": self.truck_count,
            "motorcycle": self.motorcycle_count,
            "ambulance": self.ambulance_count,
            "total_vehicles": self.total_vehicles,
            "average_speed": self.average_speed,
            "density_pct": self.density_pct,
            "detections": json.loads(self.detections_json) if self.detections_json else []
        }


class TrafficPredictionDB(Base):
    """Short-Term Forecast Congestion Data."""
    __tablename__ = "traffic_predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    intersection_code = Column(String(50), nullable=False, index=True)
    min_5_score = Column(Float, default=0.0)
    min_10_score = Column(Float, default=0.0)
    min_15_score = Column(Float, default=0.0)
    min_30_score = Column(Float, default=0.0)
    predicted_los = Column(String(10), default="A")
    trend_summary = Column(Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "intersection_code": self.intersection_code,
            "forecast": {
                "5_min": self.min_5_score,
                "10_min": self.min_10_score,
                "15_min": self.min_15_score,
                "30_min": self.min_30_score
            },
            "predicted_los": self.predicted_los,
            "trend_summary": self.trend_summary
        }


class PollutionLogDB(Base):
    """Vehicle Emissions & Carbon Footprint Logs."""
    __tablename__ = "pollution_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    intersection_code = Column(String(50), nullable=False, index=True)
    co2_kg_hr = Column(Float, default=0.0)
    nox_g_hr = Column(Float, default=0.0)
    pm25_g_hr = Column(Float, default=0.0)
    fuel_liters_hr = Column(Float, default=0.0)
    eco_index = Column(Float, default=85.0)

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "intersection_code": self.intersection_code,
            "co2_kg_hr": self.co2_kg_hr,
            "nox_g_hr": self.nox_g_hr,
            "pm25_g_hr": self.pm25_g_hr,
            "fuel_liters_hr": self.fuel_liters_hr,
            "eco_index": self.eco_index
        }


class EmergencyEventDB(Base):
    """Emergency Vehicle & Green Corridor Events."""
    __tablename__ = "emergency_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    intersection_code = Column(String(50), nullable=False, index=True)
    vehicle_type = Column(String(50), default="AMBULANCE") # AMBULANCE, FIRE_TRUCK, POLICE
    priority = Column(Integer, default=10) # 1-10 scale
    active = Column(Boolean, default=True)
    route_corridor_json = Column(Text, nullable=True) # Linked intersection codes
    status_notes = Column(Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "intersection_code": self.intersection_code,
            "vehicle_type": self.vehicle_type,
            "priority": self.priority,
            "active": self.active,
            "route_corridor": json.loads(self.route_corridor_json) if self.route_corridor_json else [],
            "status_notes": self.status_notes
        }


class DecisionLogDB(Base):
    """Explainable AI (XAI) Decision Logs."""
    __tablename__ = "decision_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    intersection_code = Column(String(50), nullable=False, index=True)
    agent_name = Column(String(100), default="Decision Agent")
    decision_type = Column(String(100), default="SIGNAL_OPTIMIZATION")
    natural_language_reasoning = Column(Text, nullable=False)
    llm_prompt_summary = Column(Text, nullable=True)
    action_taken = Column(Text, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "intersection_code": self.intersection_code,
            "agent_name": self.agent_name,
            "decision_type": self.decision_type,
            "reasoning": self.natural_language_reasoning,
            "prompt_summary": self.llm_prompt_summary,
            "action_taken": self.action_taken
        }


class TrafficDataDB(Base):
    """Raw incoming sensor telemetry table (Legacy compatibility)."""
    __tablename__ = "traffic_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    road_name = Column(String(100), nullable=False, index=True)
    vehicle_count = Column(Integer, nullable=False)
    average_speed = Column(Float, nullable=False)
    road_occupancy_pct = Column(Float, default=50.0)
    weather = Column(String(50), default="Clear")
    accident = Column(Boolean, default=False)
    emergency_vehicle = Column(Boolean, default=False)
    emergency_type = Column(String(50), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "road": self.road_name,
            "vehicles": self.vehicle_count,
            "average_speed": self.average_speed,
            "road_occupancy_pct": self.road_occupancy_pct,
            "weather": self.weather,
            "accident": self.accident,
            "emergency_vehicle": self.emergency_vehicle,
            "emergency_type": self.emergency_type
        }


class TrafficReportDB(Base):
    """Processed agent reports table (Legacy compatibility)."""
    __tablename__ = "traffic_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    road_name = Column(String(100), nullable=False, index=True)
    density = Column(String(50), nullable=False)
    congestion_score = Column(Float, default=0.0)
    signal_mode = Column(String(50), default="Standard")
    green_corridor_active = Column(Boolean, default=False)
    full_report_json = Column(Text, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "road_name": self.road_name,
            "density": self.density,
            "congestion_score": self.congestion_score,
            "signal_mode": self.signal_mode,
            "green_corridor_active": self.green_corridor_active,
            "full_report": json.loads(self.full_report_json) if self.full_report_json else {}
        }


class AlertDB(Base):
    """System and Citizen Alerts table."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    road_name = Column(String(100), nullable=False)
    alternate_route = Column(String(200), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "road_name": self.road_name,
            "alternate_route": self.alternate_route
        }


class AnalyticsDB(Base):
    """Historical traffic analytics table."""
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    road_name = Column(String(100), nullable=False, index=True)
    total_vehicles = Column(Integer, nullable=False)
    average_speed = Column(Float, nullable=False)
    congestion_index = Column(Float, nullable=False)
    carbon_emission_kg = Column(Float, nullable=False)
    road_performance_score = Column(Float, nullable=False)
    summary_notes = Column(Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "road_name": self.road_name,
            "total_vehicles": self.total_vehicles,
            "average_speed": self.average_speed,
            "congestion_index": self.congestion_index,
            "carbon_emission_kg": self.carbon_emission_kg,
            "road_performance_score": self.road_performance_score,
            "summary_notes": self.summary_notes
        }
