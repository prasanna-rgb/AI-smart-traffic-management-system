"""
Database Session Management & Data Access Layer (SQLAlchemy ORM with PostgreSQL/SQLite fallback).
"""
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from config.settings import DATABASE_URL, SQLITE_URL
from database.models import (
    Base,
    IntersectionDB,
    VisionMetricDB,
    TrafficPredictionDB,
    PollutionLogDB,
    EmergencyEventDB,
    DecisionLogDB,
    TrafficDataDB,
    TrafficReportDB,
    AlertDB,
    AnalyticsDB,
    DriverSafetyLogDB
)


logger = logging.getLogger("smart_traffic_ai.database")

# Initialize Engine with Fallback
try:
    if "postgresql" in DATABASE_URL:
        logger.info(f"Attempting to connect to PostgreSQL database: {DATABASE_URL}")
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        with engine.connect() as conn:
            pass
        logger.info("Successfully connected to PostgreSQL database.")
    else:
        raise Exception("Using SQLite fallback")
except Exception as e:
    logger.warning(f"PostgreSQL connection fallback to SQLite: {SQLITE_URL}")
    engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create all database tables and seed initial intersection nodes if missing."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        existing_intersections = session.query(IntersectionDB).count()
        if existing_intersections == 0:
            logger.info("Seeding initial smart intersection network nodes...")
            intersections = [
                IntersectionDB(code="INT-01", name="Downtown Central Hub (5th & Main)", location_lat=37.7749, location_lng=-122.4194, total_lanes=4, signal_mode="AI_AUTO", active_phase="NORTH_SOUTH_GREEN", ns_green_timer=45, ew_green_timer=25),
                IntersectionDB(code="INT-02", name="Broadway Expressway Junction", location_lat=37.7833, location_lng=-122.4167, total_lanes=6, signal_mode="AI_AUTO", active_phase="EAST_WEST_GREEN", ns_green_timer=30, ew_green_timer=50),
                IntersectionDB(code="INT-03", name="Hospital Emergency Corridor (Oak St)", location_lat=37.7690, location_lng=-122.4480, total_lanes=4, signal_mode="AI_AUTO", active_phase="NORTH_SOUTH_GREEN", ns_green_timer=60, ew_green_timer=20),
                IntersectionDB(code="INT-04", name="Industrial Park & Port Way", location_lat=37.7510, location_lng=-122.3900, total_lanes=4, signal_mode="AI_AUTO", active_phase="NORTH_SOUTH_GREEN", ns_green_timer=35, ew_green_timer=35)
            ]
            session.add_all(intersections)
            session.commit()
            logger.info("Successfully seeded 4 smart intersections.")
    except Exception as err:
        session.rollback()
        logger.error(f"Error during DB initialization seed: {err}")
    finally:
        session.close()


def get_db():
    """FastAPI Dependency for DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- CRUD HELPERS ---

def get_all_intersections(db: Session) -> List[Dict[str, Any]]:
    nodes = db.query(IntersectionDB).all()
    return [node.to_dict() for node in nodes]


def get_intersection(db: Session, code: str) -> Optional[Dict[str, Any]]:
    node = db.query(IntersectionDB).filter(IntersectionDB.code == code).first()
    return node.to_dict() if node else None


def update_intersection_signal(db: Session, code: str, mode: str, phase: str, ns_timer: int, ew_timer: int):
    node = db.query(IntersectionDB).filter(IntersectionDB.code == code).first()
    if node:
        node.signal_mode = mode
        node.active_phase = phase
        node.ns_green_timer = ns_timer
        node.ew_green_timer = ew_timer
        db.commit()
        return node.to_dict()
    return None


def save_vision_metric(db: Session, metrics_data: Dict[str, Any]):
    record = VisionMetricDB(
        intersection_code=metrics_data.get("intersection_code", "INT-01"),
        car_count=metrics_data.get("car", 0),
        bus_count=metrics_data.get("bus", 0),
        truck_count=metrics_data.get("truck", 0),
        motorcycle_count=metrics_data.get("motorcycle", 0),
        ambulance_count=metrics_data.get("ambulance", 0),
        total_vehicles=metrics_data.get("total_vehicles", 0),
        average_speed=metrics_data.get("average_speed", 40.0),
        density_pct=metrics_data.get("density_pct", 0.0),
        detections_json=json.dumps(metrics_data.get("detections", []))
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record.to_dict()


def get_latest_vision_metrics(db: Session, code: str = "INT-01", limit: int = 10):
    records = db.query(VisionMetricDB).filter(VisionMetricDB.intersection_code == code).order_by(VisionMetricDB.timestamp.desc()).limit(limit).all()
    return [r.to_dict() for r in records]


def save_prediction(db: Session, pred_data: Dict[str, Any]):
    forecast = pred_data.get("forecast", {})
    record = TrafficPredictionDB(
        intersection_code=pred_data.get("intersection_code", "INT-01"),
        min_5_score=forecast.get("5_min", 0.0),
        min_10_score=forecast.get("10_min", 0.0),
        min_15_score=forecast.get("15_min", 0.0),
        min_30_score=forecast.get("30_min", 0.0),
        predicted_los=pred_data.get("predicted_los", "A"),
        trend_summary=pred_data.get("trend_summary", "Stable flow")
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record.to_dict()


def save_pollution_log(db: Session, pol_data: Dict[str, Any]):
    record = PollutionLogDB(
        intersection_code=pol_data.get("intersection_code", "INT-01"),
        co2_kg_hr=pol_data.get("co2_kg_hr", 0.0),
        nox_g_hr=pol_data.get("nox_g_hr", 0.0),
        pm25_g_hr=pol_data.get("pm25_g_hr", 0.0),
        fuel_liters_hr=pol_data.get("fuel_liters_hr", 0.0),
        eco_index=pol_data.get("eco_index", 85.0)
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record.to_dict()


def save_emergency_event(db_or_data: Any, emergency_data: Optional[Dict[str, Any]] = None):
    """Flexible emergency event persistence supporting both 1-arg (dict) and 2-arg (db, dict) call patterns."""
    if isinstance(db_or_data, dict) and emergency_data is None:
        data = db_or_data
        db = SessionLocal()
        should_close = True
    else:
        db = db_or_data
        data = emergency_data or {}
        should_close = False

    try:
        loc = data.get("location", {})
        record = EmergencyEventDB(
            timestamp=datetime.utcnow(),
            event_id=data.get("event_id", f"EVT-{uuid.uuid4().hex[:6].upper()}"),
            event_type=data.get("event_type", "ACCIDENT"),
            severity=data.get("severity", "CRITICAL"),
            road_name=data.get("road_name", data.get("road", "Main Road")),
            latitude=float(loc.get("latitude", 13.0827)),
            longitude=float(loc.get("longitude", 80.2707)),
            emergency_vehicle_type=data.get("emergency_vehicle_type", "AMBULANCE"),
            signal_before=data.get("signal_before", "Green 30s / Red 30s"),
            signal_after=data.get("signal_after", "Green 50s / Red 15s"),
            green_time_before=int(data.get("green_time_before", 30)),
            green_time_after=int(data.get("green_time_after", 50)),
            voice_alert_sent=bool(data.get("voice_alert_sent", True)),
            citizen_alert_sent=bool(data.get("citizen_alert_sent", True)),
            status=data.get("status", "ACTIVE")
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record.to_dict()
    except Exception as e:
        logger.warning(f"Schema fallback saving emergency event: {e}")
        try:
            db.rollback()
            record = EmergencyEventDB(
                intersection_code=data.get("intersection_code", "INT-01"),
                vehicle_type=data.get("vehicle_type", "AMBULANCE"),
                priority=data.get("priority", 10),
                active=data.get("active", True),
                route_corridor_json=json.dumps(data.get("route_corridor", ["INT-01", "INT-03"])),
                status_notes=data.get("status_notes", "Emergency Vehicle Green Corridor Cleared")
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            return record.to_dict()
        except Exception as inner_e:
            logger.error(f"Failed to save emergency event: {inner_e}")
            return None
    finally:
        if should_close and db:
            db.close()



def save_decision_log(db: Session, decision_data: Dict[str, Any]):
    record = DecisionLogDB(
        intersection_code=decision_data.get("intersection_code", "INT-01"),
        agent_name=decision_data.get("agent_name", "Decision Agent"),
        decision_type=decision_data.get("decision_type", "SIGNAL_OPTIMIZATION"),
        natural_language_reasoning=decision_data.get("natural_language_reasoning", ""),
        llm_prompt_summary=decision_data.get("llm_prompt_summary", ""),
        action_taken=decision_data.get("action_taken", "")
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record.to_dict()


def get_latest_decision_logs(db: Session, limit: int = 20):
    logs = db.query(DecisionLogDB).order_by(DecisionLogDB.timestamp.desc()).limit(limit).all()
    return [l.to_dict() for l in logs]


# Legacy wrapper methods for backwards compatibility
def save_traffic_input(data: Dict[str, Any]):
    db = SessionLocal()
    try:
        record = TrafficDataDB(
            road_name=data.get("road", "Main Road"),
            vehicle_count=data.get("vehicles", 50),
            average_speed=data.get("average_speed", 40.0),
            road_occupancy_pct=data.get("road_occupancy_pct", 50.0),
            weather=data.get("weather", "Clear"),
            accident=data.get("accident", False),
            emergency_vehicle=data.get("emergency_vehicle", False),
            emergency_type=data.get("emergency_type")
        )
        db.add(record)
        db.commit()
    finally:
        db.close()


def save_traffic_report(road_name: str, density: str, congestion_score: float, signal_mode: str, green_corridor: bool, report_dict: dict):
    db = SessionLocal()
    try:
        record = TrafficReportDB(
            road_name=road_name,
            density=density,
            congestion_score=congestion_score,
            signal_mode=signal_mode,
            green_corridor_active=green_corridor,
            full_report_json=json.dumps(report_dict)
        )
        db.add(record)
        db.commit()
    finally:
        db.close()


def save_alert(alert_type: str, severity: str, title: str, message: str, road_name: str, alternate_route: str = None):
    db = SessionLocal()
    try:
        record = AlertDB(
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            road_name=road_name,
            alternate_route=alternate_route
        )
        db.add(record)
        db.commit()
    finally:
        db.close()


def save_analytics(road_name: str, vehicles: int, avg_speed: float, congestion_index: float, carbon_kg: float, performance: float, notes: str):
    db = SessionLocal()
    try:
        record = AnalyticsDB(
            road_name=road_name,
            total_vehicles=vehicles,
            average_speed=avg_speed,
            congestion_index=congestion_index,
            carbon_emission_kg=carbon_kg,
            road_performance_score=performance,
            summary_notes=notes
        )
        db.add(record)
        db.commit()
    finally:
        db.close()


def get_latest_traffic_data(limit: int = 10):
    db = SessionLocal()
    try:
        records = db.query(TrafficDataDB).order_by(TrafficDataDB.timestamp.desc()).limit(limit).all()
        return [r.to_dict() for r in records]
    finally:
        db.close()


def get_latest_reports(limit: int = 10):
    db = SessionLocal()
    try:
        reports = db.query(TrafficReportDB).order_by(TrafficReportDB.timestamp.desc()).limit(limit).all()
        return [r.to_dict() for r in reports]
    finally:
        db.close()


def get_active_alerts(limit: int = 20):
    db = SessionLocal()
    try:
        alerts = db.query(AlertDB).order_by(AlertDB.timestamp.desc()).limit(limit).all()
        return [a.to_dict() for a in alerts]
    finally:
        db.close()


def get_all_alerts(limit: int = 20):
    return get_active_alerts(limit=limit)


def get_analytics_summary(limit: int = 10):
    db = SessionLocal()
    try:
        analytics = db.query(AnalyticsDB).order_by(AnalyticsDB.timestamp.desc()).limit(limit).all()
        return [a.to_dict() for a in analytics]
    finally:
        db.close()


def save_driver_safety_log(db_session: Optional[Session], data: dict):
    """Persist driver safety report to database."""
    should_close = False
    if db_session is None:
        db_session = SessionLocal()
        should_close = True
    try:
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
        db_session.add(record)
        db_session.commit()
        return record.to_dict()
    finally:
        if should_close:
            db_session.close()


def get_driver_safety_logs(limit: int = 20):
    db = SessionLocal()
    try:
        logs = db.query(DriverSafetyLogDB).order_by(DriverSafetyLogDB.timestamp.desc()).limit(limit).all()
        return [l.to_dict() for l in logs]
    finally:
        db.close()

