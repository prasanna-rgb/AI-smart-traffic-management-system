"""
SQLAlchemy ORM Models for Database Tables.
"""
from datetime import datetime
import json
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class TrafficDataDB(Base):
    """Raw incoming sensor telemetry table."""
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
    """Processed agent reports and decision logs table."""
    __tablename__ = "traffic_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    road_name = Column(String(100), nullable=False, index=True)
    density = Column(String(50), nullable=False) # Low, Medium, High, Critical
    congestion_score = Column(Float, default=0.0)
    signal_mode = Column(String(50), default="Standard")
    green_corridor_active = Column(Boolean, default=False)
    full_report_json = Column(Text, nullable=False)

    def to_dict(self):
        parsed_report = {}
        if self.full_report_json:
            try:
                parsed_report = json.loads(self.full_report_json)
                if isinstance(parsed_report, str):
                    parsed_report = json.loads(parsed_report)
            except Exception:
                parsed_report = {}
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "road_name": self.road_name,
            "density": self.density,
            "congestion_score": self.congestion_score,
            "signal_mode": self.signal_mode,
            "green_corridor_active": self.green_corridor_active,
            "full_report": parsed_report if isinstance(parsed_report, dict) else {}
        }



class AlertDB(Base):
    """System and Citizen Alerts table."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    alert_type = Column(String(50), nullable=False) # CITIZEN, EMERGENCY, TRAFFIC
    severity = Column(String(20), nullable=False) # INFO, WARNING, CRITICAL, EMERGENCY
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
    """Historical traffic and carbon emissions analytics table."""
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


class DriverSafetyLogDB(Base):
    """Driver Behavior, Safety Scores & Violations Log Table."""
    __tablename__ = "driver_safety_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    vehicle_id = Column(String(100), nullable=False, index=True)
    road_id = Column(String(100), nullable=False, index=True)
    latitude = Column(Float, default=13.0827)
    longitude = Column(Float, default=80.2707)
    safety_score = Column(Integer, nullable=False)
    risk_level = Column(String(50), nullable=False) # LOW, MEDIUM, HIGH, CRITICAL
    total_violations = Column(Integer, default=0)
    violations_json = Column(Text, nullable=False)
    primary_hazard = Column(String(250), nullable=True)
    recommendation = Column(Text, nullable=True)
    prediction_json = Column(Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "vehicle_id": self.vehicle_id,
            "road_id": self.road_id,
            "location": {
                "latitude": self.latitude,
                "longitude": self.longitude
            },
            "safety_score": self.safety_score,
            "risk_level": self.risk_level,
            "total_violations": self.total_violations,
            "violations": json.loads(self.violations_json) if self.violations_json else {},
            "primary_hazard": self.primary_hazard,
            "recommendation": self.recommendation,
            "risk_prediction": json.loads(self.prediction_json) if self.prediction_json else {}
        }


class EmergencyEventDB(Base):
    """Emergency Events & Response Logs Table."""
    __tablename__ = "emergency_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    event_id = Column(String(100), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    severity = Column(String(50), nullable=False)
    road_name = Column(String(100), nullable=False, index=True)
    latitude = Column(Float, default=13.0827)
    longitude = Column(Float, default=80.2707)
    emergency_vehicle_type = Column(String(50), default="NONE")
    signal_before = Column(String(50), default="Green 30s / Red 30s")
    signal_after = Column(String(50), default="Green 50s / Red 15s")
    green_time_before = Column(Integer, default=30)
    green_time_after = Column(Integer, default=50)
    voice_alert_sent = Column(Boolean, default=False)
    citizen_alert_sent = Column(Boolean, default=False)
    status = Column(String(50), default="ACTIVE")

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "severity": self.severity,
            "road_name": self.road_name,
            "location": {
                "latitude": self.latitude,
                "longitude": self.longitude
            },
            "emergency_vehicle_type": self.emergency_vehicle_type,
            "signal_before": self.signal_before,
            "signal_after": self.signal_after,
            "green_time_before": self.green_time_before,
            "green_time_after": self.green_time_after,
            "voice_alert_sent": self.voice_alert_sent,
            "citizen_alert_sent": self.citizen_alert_sent,
            "status": self.status
        }


class ScenarioSimulationDB(Base):
    """Traffic Scenario Simulations & Decision Intelligence Table."""
    __tablename__ = "scenario_simulations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    scenario_id = Column(String(100), nullable=False, index=True)
    road_name = Column(String(100), nullable=False, index=True)
    current_conditions_json = Column(Text, nullable=False)
    scenario_action = Column(String(200), nullable=False)
    predicted_congestion = Column(Integer, nullable=False)
    predicted_delay = Column(Integer, nullable=False)
    predicted_emergency_time = Column(Integer, nullable=False)
    predicted_carbon = Column(String(50), default="MEDIUM")
    decision_score = Column(Float, nullable=False)
    selected = Column(Boolean, default=False)
    reason = Column(Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "scenario_id": self.scenario_id,
            "road_name": self.road_name,
            "current_conditions": json.loads(self.current_conditions_json) if self.current_conditions_json else {},
            "scenario_action": self.scenario_action,
            "predicted_congestion": self.predicted_congestion,
            "predicted_delay": self.predicted_delay,
            "predicted_emergency_time": self.predicted_emergency_time,
            "predicted_carbon": self.predicted_carbon,
            "decision_score": self.decision_score,
            "selected": self.selected,
            "reason": self.reason
        }


class EmergencyResourceAllocationDB(Base):
    """Emergency Resource Allocation DB Table."""
    __tablename__ = "emergency_resource_allocations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    allocation_id = Column(String(100), nullable=False, index=True)
    accident_id = Column(String(100), nullable=False, index=True)
    ambulance_id = Column(String(100), nullable=False)
    hospital_id = Column(String(100), nullable=False)
    hospital_name = Column(String(150), nullable=False)
    accident_location = Column(String(150), nullable=False)
    ambulance_eta = Column(Integer, nullable=False)
    hospital_eta = Column(Integer, nullable=False)
    total_response_time = Column(Integer, nullable=False)
    decision_score = Column(Float, nullable=False)
    route = Column(String(200), nullable=False)
    green_corridor_status = Column(String(50), default="ACTIVE")
    allocation_status = Column(String(50), default="ALLOCATED")
    details_json = Column(Text, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "allocation_id": self.allocation_id,
            "accident_id": self.accident_id,
            "selected_ambulance": {
                "ambulance_id": self.ambulance_id,
                "response_time_minutes": self.ambulance_eta
            },
            "selected_hospital": {
                "hospital_id": self.hospital_id,
                "hospital_name": self.hospital_name,
                "travel_time_minutes": self.hospital_eta
            },
            "accident_location": self.accident_location,
            "total_estimated_time": self.total_response_time,
            "decision_score": self.decision_score,
            "recommended_route": self.route,
            "green_corridor_status": self.green_corridor_status,
            "allocation_status": self.allocation_status,
            "details": json.loads(self.details_json) if self.details_json else {}
        }


class FloodMonitoringDB(Base):
    """Flood Monitoring and Waterlogging Risk Table."""
    __tablename__ = "flood_monitoring_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    record_id = Column(String(100), nullable=False, index=True)
    road_id = Column(String(100), nullable=False, index=True)
    road_name = Column(String(100), nullable=False, index=True)
    latitude = Column(Float, default=13.0827)
    longitude = Column(Float, default=80.2707)
    rainfall_mm_per_hour = Column(Float, nullable=False)
    flood_risk_score = Column(Integer, nullable=False)
    risk_level = Column(String(50), nullable=False) # LOW, MODERATE, HIGH, VERY HIGH, CRITICAL
    traffic_density = Column(String(50), default="MEDIUM")
    water_level = Column(String(50), default="UNAVAILABLE")
    predicted_waterlogging = Column(Boolean, default=False)
    estimated_time_to_waterlogging = Column(String(50), default="None")
    recommended_action = Column(Text, nullable=False)
    alternate_route = Column(String(200), nullable=True)
    details_json = Column(Text, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "record_id": self.record_id,
            "road_id": self.road_id,
            "road_name": self.road_name,
            "location": {
                "latitude": self.latitude,
                "longitude": self.longitude
            },
            "rainfall_mm_per_hour": self.rainfall_mm_per_hour,
            "flood_risk_score": self.flood_risk_score,
            "risk_level": self.risk_level,
            "traffic_density": self.traffic_density,
            "water_level": self.water_level,
            "predicted_waterlogging": self.predicted_waterlogging,
            "estimated_time_to_waterlogging": self.estimated_time_to_waterlogging,
            "recommended_action": self.recommended_action,
            "alternate_route": self.alternate_route,
            "details": json.loads(self.details_json) if self.details_json else {}
        }





