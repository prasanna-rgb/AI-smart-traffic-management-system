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
