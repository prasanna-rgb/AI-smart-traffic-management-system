"""
Database Connection and Data Access Layer.
"""
import json
from datetime import datetime
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.settings import DATABASE_URL
from database.models import Base, TrafficDataDB, TrafficReportDB, AlertDB, AnalyticsDB, DriverSafetyLogDB


# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database schema tables."""
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db():
    """Provide a transactional scope around a series of database operations."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def save_traffic_input(data: dict) -> TrafficDataDB:
    """Persist raw telemetry input to database."""
    with get_db() as db:
        record = TrafficDataDB(
            timestamp=datetime.utcnow(),
            road_name=data.get("road", "Main Road"),
            vehicle_count=data.get("vehicle_count", data.get("vehicles", 0)),
            average_speed=data.get("average_speed", 30.0),
            road_occupancy_pct=data.get("road_occupancy_pct", 50.0),
            weather=data.get("weather", "Clear"),
            accident=data.get("accident", False),
            emergency_vehicle=data.get("emergency_vehicle", False),
            emergency_type=data.get("emergency_type")
        )
        db.add(record)
        db.flush()
        db.refresh(record)
        return record


def save_traffic_report(road_name: str, density: str, congestion_score: float, signal_mode: str, green_corridor: bool, report_dict: dict) -> TrafficReportDB:
    """Persist processed Crew report to database."""
    with get_db() as db:
        record = TrafficReportDB(
            timestamp=datetime.utcnow(),
            road_name=road_name,
            density=density,
            congestion_score=congestion_score,
            signal_mode=signal_mode,
            green_corridor_active=green_corridor,
            full_report_json=json.dumps(report_dict)
        )
        db.add(record)
        db.flush()
        db.refresh(record)
        return record


def save_alert(alert_type: str, severity: str, title: str, message: str, road_name: str, alternate_route: str = None) -> AlertDB:
    """Persist system or citizen alert to database."""
    with get_db() as db:
        record = AlertDB(
            timestamp=datetime.utcnow(),
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            road_name=road_name,
            alternate_route=alternate_route
        )
        db.add(record)
        db.flush()
        db.refresh(record)
        return record


def save_analytics(road_name: str, vehicles: int, avg_speed: float, congestion_index: float, carbon_kg: float, performance: float, notes: str) -> AnalyticsDB:
    """Persist analytics entry to database."""
    with get_db() as db:
        record = AnalyticsDB(
            timestamp=datetime.utcnow(),
            road_name=road_name,
            total_vehicles=vehicles,
            average_speed=avg_speed,
            congestion_index=congestion_index,
            carbon_emission_kg=carbon_kg,
            road_performance_score=performance,
            summary_notes=notes
        )
        db.add(record)
        db.flush()
        db.refresh(record)
        return record


def get_latest_traffic_data(limit: int = 10):
    """Retrieve recent traffic telemetry entries."""
    with get_db() as db:
        records = db.query(TrafficDataDB).order_by(TrafficDataDB.timestamp.desc()).limit(limit).all()
        return [r.to_dict() for r in records]


def get_latest_reports(limit: int = 10):
    """Retrieve recent Crew reports."""
    with get_db() as db:
        records = db.query(TrafficReportDB).order_by(TrafficReportDB.timestamp.desc()).limit(limit).all()
        return [r.to_dict() for r in records]


def get_active_alerts(limit: int = 10):
    """Retrieve recent alerts."""
    with get_db() as db:
        records = db.query(AlertDB).order_by(AlertDB.timestamp.desc()).limit(limit).all()
        return [r.to_dict() for r in records]


def get_analytics_summary(limit: int = 50):
    """Retrieve historical analytics."""
    with get_db() as db:
        records = db.query(AnalyticsDB).order_by(AnalyticsDB.timestamp.desc()).limit(limit).all()
        return [r.to_dict() for r in records]


def save_driver_safety_log(data: dict) -> DriverSafetyLogDB:
    """Persist driver safety assessment and violations to database."""
    with get_db() as db:
        loc = data.get("location", {})
        record = DriverSafetyLogDB(
            timestamp=datetime.utcnow(),
            vehicle_id=data.get("vehicle_id", "VH101"),
            road_id=data.get("road_id", data.get("road", "Main Road")),
            latitude=float(loc.get("latitude", 13.0827)),
            longitude=float(loc.get("longitude", 80.2707)),
            safety_score=int(data.get("safety_score", 100)),
            risk_level=str(data.get("risk_level", "LOW")),
            total_violations=int(data.get("total_violations", 0)),
            violations_json=json.dumps(data.get("violations", {})),
            primary_hazard=data.get("primary_hazard", "None"),
            recommendation=data.get("recommendation", ""),
            prediction_json=json.dumps(data.get("risk_prediction", {}))
        )
        db.add(record)
        db.flush()
        db.refresh(record)
        return record


def get_driver_safety_logs(limit: int = 20):
    """Retrieve recent driver safety logs."""
    with get_db() as db:
        records = db.query(DriverSafetyLogDB).order_by(DriverSafetyLogDB.timestamp.desc()).limit(limit).all()
        return [r.to_dict() for r in records]

