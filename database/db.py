"""
Database Connection and Data Access Layer.
"""
import json
import uuid
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config.settings import DATABASE_URL
from database.models import (
    Base, TrafficDataDB, TrafficReportDB, AlertDB, AnalyticsDB, 
    DriverSafetyLogDB, EmergencyEventDB, ScenarioSimulationDB, 
    EmergencyResourceAllocationDB, FloodMonitoringDB
)


def save_emergency_allocation(data: dict) -> Optional[EmergencyResourceAllocationDB]:
    """Persist emergency resource allocation to database."""
    try:
        with get_db() as db:
            amb = data.get("selected_ambulance", {})
            hosp = data.get("selected_hospital", {})
            record = EmergencyResourceAllocationDB(
                timestamp=datetime.utcnow(),
                allocation_id=data.get("allocation_id", f"ALLOC-{uuid.uuid4().hex[:6].upper()}"),
                accident_id=data.get("accident_id", "ACC101"),
                ambulance_id=amb.get("ambulance_id", "AMB001"),
                hospital_id=hosp.get("hospital_id", "H001"),
                hospital_name=hosp.get("hospital_name", "City Emergency Hospital"),
                accident_location=data.get("accident_location", "Main Road"),
                ambulance_eta=int(amb.get("response_time_minutes", 6)),
                hospital_eta=int(hosp.get("travel_time_minutes", 9)),
                total_response_time=int(data.get("total_estimated_time", 15)),
                decision_score=float(data.get("decision_score", 90.0)),
                route=data.get("recommended_route", "Main Road -> Hospital"),
                green_corridor_status=data.get("green_corridor_status", "ACTIVE"),
                allocation_status=data.get("allocation_status", "ALLOCATED"),
                details_json=json.dumps(data)
            )
            db.add(record)
            db.flush()
            db.refresh(record)
            return record
    except Exception as e:
        logger.error(f"Failed to save emergency allocation: {e}")
        return None

def get_recent_emergency_allocations(limit: int = 10):
    """Retrieve recent emergency resource allocation logs."""
    try:
        with get_db() as db:
            records = db.query(EmergencyResourceAllocationDB).order_by(EmergencyResourceAllocationDB.timestamp.desc()).limit(limit).all()
            return [r.to_dict() for r in records]
    except Exception:
        return []


def save_scenario_simulation(data: dict) -> Optional[ScenarioSimulationDB]:
    """Persist scenario evaluation log to database."""
    try:
        with get_db() as db:
            record = ScenarioSimulationDB(
                timestamp=datetime.utcnow(),
                scenario_id=data.get("scenario_id", f"SCEN-{uuid.uuid4().hex[:6].upper()}"),
                road_name=data.get("road_name", data.get("road", "Main Road")),
                current_conditions_json=json.dumps(data.get("current_conditions", {})),
                scenario_action=data.get("scenario_action", data.get("action", "Standard Operations")),
                predicted_congestion=int(data.get("predicted_congestion", 40)),
                predicted_delay=int(data.get("predicted_delay", 5)),
                predicted_emergency_time=int(data.get("predicted_emergency_time", 8)),
                predicted_carbon=str(data.get("predicted_carbon", "MEDIUM")).upper(),
                decision_score=float(data.get("decision_score", 50.0)),
                selected=bool(data.get("selected", False)),
                reason=data.get("reason", "")
            )
            db.add(record)
            db.flush()
            db.refresh(record)
            return record
    except Exception as err:
        logger.warning(f"Failed to persist scenario simulation log: {err}")
        return None


def get_recent_scenario_simulations(limit: int = 20):
    """Retrieve recent scenario simulations."""
    try:
        with get_db() as db:
            records = db.query(ScenarioSimulationDB).order_by(ScenarioSimulationDB.timestamp.desc()).limit(limit).all()
            return [r.to_dict() for r in records]
    except Exception:
        return []


logger = logging.getLogger("smart_traffic_ai.database")

try:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception:
    SQLITE_FALLBACK = "sqlite:///smart_traffic.db"
    engine = create_engine(SQLITE_FALLBACK, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database schema tables with automatic fallback."""
    global engine, SessionLocal
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.warning(f"PostgreSQL connection fallback to SQLite: {e}")
        SQLITE_FALLBACK = "sqlite:///smart_traffic.db"
        engine = create_engine(SQLITE_FALLBACK, connect_args={"check_same_thread": False})
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
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
            road_name=data.get("road_name", data.get("road", "Main Road")),
            vehicle_count=data.get("vehicle_count", data.get("vehicles", 0)),
            average_speed=data.get("average_speed", 30.0),
            road_occupancy_pct=data.get("road_occupancy_pct", 50.0),
            weather=data.get("weather", "Clear"),
            accident=data.get("accident_status", data.get("accident", False)),
            emergency_vehicle=data.get("emergency_vehicle_status", data.get("emergency_vehicle", False)),
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


def save_emergency_event(event_data: dict) -> Optional[EmergencyEventDB]:
    """Persist emergency response event to database with auto-migration safety."""
    loc = event_data.get("location", {})
    evt_args = dict(
        timestamp=datetime.utcnow(),
        event_id=event_data.get("event_id", f"EVT-{uuid.uuid4().hex[:6].upper()}"),
        event_type=event_data.get("event_type", "ACCIDENT"),
        severity=event_data.get("severity", "CRITICAL"),
        road_name=event_data.get("road_name", "Main Road"),
        latitude=float(loc.get("latitude", 13.0827)),
        longitude=float(loc.get("longitude", 80.2707)),
        emergency_vehicle_type=event_data.get("emergency_vehicle_type", "AMBULANCE"),
        signal_before=event_data.get("signal_before", "Green 30s / Red 30s"),
        signal_after=event_data.get("signal_after", "Green 50s / Red 15s"),
        green_time_before=int(event_data.get("green_time_before", 30)),
        green_time_after=int(event_data.get("green_time_after", 50)),
        voice_alert_sent=bool(event_data.get("voice_alert_sent", True)),
        citizen_alert_sent=bool(event_data.get("citizen_alert_sent", True)),
        status=event_data.get("status", "ACTIVE")
    )
    
    try:
        with get_db() as db:
            record = EmergencyEventDB(**evt_args)
            db.add(record)
            db.flush()
            db.refresh(record)
            return record
    except Exception as e:
        logger.warning(f"Legacy emergency_events schema mismatch: {e}. Dropping and recreating table.")
        try:
            with engine.begin() as conn:
                conn.execute(text("DROP TABLE IF EXISTS emergency_events"))
            EmergencyEventDB.__table__.create(bind=engine, checkfirst=True)
            with get_db() as db:
                record = EmergencyEventDB(**evt_args)
                db.add(record)
                db.flush()
                db.refresh(record)
                return record
        except Exception as inner_e:
            logger.error(f"Failed to persist emergency event: {inner_e}")
            return None


def get_active_emergency_events(limit: int = 10):
    """Retrieve active emergency events from database."""
    try:
        with get_db() as db:
            records = db.query(EmergencyEventDB).order_by(EmergencyEventDB.timestamp.desc()).limit(limit).all()
            return [r.to_dict() for r in records]
    except Exception:
        return []


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


def save_flood_monitoring_log(data: dict) -> Optional[FloodMonitoringDB]:
    """Persist flood and waterlogging monitoring report to database."""
    try:
        with get_db() as db:
            loc = data.get("location", {})
            record = FloodMonitoringDB(
                timestamp=datetime.utcnow(),
                record_id=data.get("record_id", f"FLD-{uuid.uuid4().hex[:6].upper()}"),
                road_id=data.get("road_id", "R101"),
                road_name=data.get("road_name", data.get("road", "Main Road")),
                latitude=float(loc.get("latitude", 13.0827)),
                longitude=float(loc.get("longitude", 80.2707)),
                rainfall_mm_per_hour=float(data.get("rainfall_mm_per_hour", 0.0)),
                flood_risk_score=int(data.get("flood_risk_score", 0)),
                risk_level=str(data.get("risk_level", "LOW")),
                traffic_density=str(data.get("traffic_density", "MEDIUM")),
                water_level=str(data.get("water_level", "UNAVAILABLE")),
                predicted_waterlogging=bool(data.get("predicted_waterlogging", False)),
                estimated_time_to_waterlogging=str(data.get("estimated_time_to_waterlogging", "None")),
                recommended_action=str(data.get("recommended_action", "Normal operations")),
                alternate_route=data.get("alternate_route"),
                details_json=json.dumps(data.get("details", data))
            )
            db.add(record)
            db.flush()
            db.refresh(record)
            return record
    except Exception as err:
        logger.warning(f"Failed to persist flood monitoring log: {err}")
        return None


def get_recent_flood_logs(limit: int = 20) -> List[dict]:
    """Retrieve recent flood monitoring logs."""
    try:
        with get_db() as db:
            records = db.query(FloodMonitoringDB).order_by(FloodMonitoringDB.timestamp.desc()).limit(limit).all()
            return [r.to_dict() for r in records]
    except Exception as err:
        logger.warning(f"Failed to fetch flood logs: {err}")
        return []

