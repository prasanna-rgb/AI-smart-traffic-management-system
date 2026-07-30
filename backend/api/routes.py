"""
FastAPI REST API Routes for Smart Traffic Management System.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except Exception:
    CV2_AVAILABLE = False

from database.db import (
    get_db,
    get_all_intersections,
    get_intersection,
    update_intersection_signal,
    get_latest_vision_metrics,
    get_latest_decision_logs,
    get_latest_reports,
    get_all_alerts,
    save_emergency_event
)
from crew import run_traffic_crew
from vision.yolo_detector import YOLOV8Detector
from vision.stream_processor import stream_processor

router = APIRouter(prefix="/api/traffic", tags=["Smart Traffic Management AI"])

# Shared YOLO Detector Instance
detector = YOLOV8Detector()


@router.get("/intersections", summary="Get all smart intersection nodes")
def list_intersections(db: Session = Depends(get_db)):
    """Retrieve state and metadata for all intersections in the smart grid."""
    return {"status": "success", "intersections": get_all_intersections(db)}


@router.get("/intersections/{code}", summary="Get specific intersection detail")
def get_intersection_detail(code: str, db: Session = Depends(get_db)):
    node = get_intersection(db, code)
    if not node:
        raise HTTPException(status_code=404, detail=f"Intersection {code} not found")
    metrics = get_latest_vision_metrics(db, code=code, limit=5)
    return {"status": "success", "intersection": node, "recent_vision_metrics": metrics}


@router.post("/detect", summary="Process uploaded frame with YOLOv8 Vision Detector")
async def detect_frame(file: UploadFile = File(...), code: str = Form("INT-01")):
    """Upload a camera image frame to run YOLOv8 detection for 5 vehicle classes."""
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    
    if CV2_AVAILABLE:
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    else:
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

    if frame is None:
        raise HTTPException(status_code=400, detail="Invalid image file format")

    annotated_frame, metrics = detector.process_frame(frame, intersection_code=code)
    b64_img = detector.encode_frame_to_base64(annotated_frame)

    return {
        "status": "success",
        "metrics": metrics,
        "annotated_frame_base64": b64_img
    }


@router.post("/run-crew", summary="Execute 6-Agent CrewAI Orchestrator Pipeline")
def execute_crew(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Trigger full 6-agent sequential execution:
    Vision -> Traffic Analysis -> Prediction -> Pollution -> Emergency -> Decision
    """
    report = run_traffic_crew(payload)
    return {"status": "success", "report": report}


@router.get("/predictions", summary="Get short-term congestion forecasts")
def get_predictions(code: str = Query("INT-01"), db: Session = Depends(get_db)):
    metrics = get_latest_vision_metrics(db, code=code, limit=1)
    current_density = metrics[0]["density_pct"] if metrics else 45.0
    from agents.prediction_agent import process_prediction_rule_based
    from agents.traffic_analysis_agent import process_traffic_analysis_rule_based
    
    vis = {"intersection_code": code, "density_pct": current_density}
    ana = process_traffic_analysis_rule_based(vis)
    pred = process_prediction_rule_based(vis, ana)
    return {"status": "success", "prediction": pred}


@router.get("/emissions", summary="Get environmental emissions estimate")
def get_emissions(code: str = Query("INT-01"), db: Session = Depends(get_db)):
    metrics = get_latest_vision_metrics(db, code=code, limit=1)
    vision_data = metrics[0] if metrics else {"total_vehicles": 35, "density_pct": 40.0}
    from agents.pollution_agent import process_pollution_rule_based
    from agents.traffic_analysis_agent import process_traffic_analysis_rule_based
    
    ana = process_traffic_analysis_rule_based(vision_data)
    pol = process_pollution_rule_based(vision_data, ana)
    return {"status": "success", "pollution": pol}


@router.post("/emergency/trigger", summary="Activate/Deactivate Emergency Green Corridor")
def trigger_emergency(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """Trigger emergency vehicle corridor preemption for designated intersection route."""
    code = payload.get("intersection_code", "INT-01")
    active = payload.get("active", True)
    vehicle_type = payload.get("vehicle_type", "AMBULANCE")

    from agents.emergency_agent import process_emergency_rule_based
    vis_data = {"intersection_code": code, "emergency_vehicle_detected": active, "fleet_breakdown": {"ambulance": 1 if active else 0}}
    emg_result = process_emergency_rule_based(vis_data, {})

    save_emergency_event(db, emg_result)

    # Re-run Decision Agent to update signal splits
    telemetry = {"intersection_code": code, "emergency_vehicle": active, "emergency_type": vehicle_type}
    report = run_traffic_crew(telemetry)

    return {"status": "success", "emergency_event": emg_result, "crew_decision": report["decision"]}


@router.post("/signals/override", summary="Manual override of traffic signal mode & timers")
def override_signal(payload: Dict[str, Any], db: Session = Depends(get_db)):
    code = payload.get("intersection_code", "INT-01")
    mode = payload.get("signal_mode", "MANUAL")
    phase = payload.get("active_phase", "NORTH_SOUTH_GREEN")
    ns_timer = payload.get("ns_green_timer", 30)
    ew_timer = payload.get("ew_green_timer", 30)

    updated_node = update_intersection_signal(db, code=code, mode=mode, phase=phase, ns_timer=ns_timer, ew_timer=ew_timer)
    if not updated_node:
        raise HTTPException(status_code=404, detail=f"Intersection {code} not found")

    return {"status": "success", "intersection": updated_node}


@router.get("/decision-logs", summary="Get Explainable AI (XAI) natural language decision logs")
def fetch_decision_logs(limit: int = 20, db: Session = Depends(get_db)):
    logs = get_latest_decision_logs(db, limit=limit)
    return {"status": "success", "decision_logs": logs}


@router.post("/sumo/sync", summary="SUMO Simulation Integration Bridge")
def sync_sumo_data(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """Bridge API to accept telemetry from SUMO (Simulation of Urban MObility)."""
    code = payload.get("intersection_code", "INT-01")
    telemetry = {
        "intersection_code": code,
        "vehicles": payload.get("vehicle_count", 40),
        "average_speed": payload.get("avg_speed_m_s", 12.0) * 3.6,
        "emergency_vehicle": payload.get("has_emergency_vehicle", False)
    }
    report = run_traffic_crew(telemetry)
    return {"status": "success", "sumo_ingested": True, "crew_report": report}


@router.post("/stream/source", summary="Switch video stream camera source")
def set_stream_source(payload: Dict[str, Any]):
    source = payload.get("source", "synthetic")
    stream_processor.start_stream(source=source)
    return {"status": "success", "active_source": source}


# --- DRIVER BEHAVIOR & SAFETY ANALYTICS ROUTES ---

@router.post("/driver-safety/analyze", summary="Analyze driver telemetry and compute Driver Safety Score")
def analyze_driver_safety(telemetry: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Analyze vehicle telemetry to detect 8 violation types, compute Driver Safety Score (0-100),
    predict future driver risk, log GPS location intelligence, and raise safety alerts.
    """
    from tools.driver_behavior_tools import DriverBehaviorTools
    from database.db import save_driver_safety_log
    
    try:
        result = DriverBehaviorTools.evaluate_telemetry(telemetry)
        save_driver_safety_log(db, result)
        return {"status": "success", "driver_safety": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze driver safety: {str(e)}")


@router.get("/driver-safety/logs", summary="Get driver safety assessment logs")
def fetch_driver_safety_logs(limit: int = 20):
    from database.db import get_driver_safety_logs
    logs = get_driver_safety_logs(limit=limit)
    return {"status": "success", "count": len(logs), "logs": logs}


@router.get("/driver-safety/test-cases", summary="Get 6 simulated driver telemetry test scenarios")
def get_driver_safety_test_scenarios():
    from tools.driver_behavior_tools import DriverBehaviorTools
    test_cases = DriverBehaviorTools.get_test_cases()
    results = []
    for tc in test_cases:
        eval_res = DriverBehaviorTools.evaluate_telemetry(tc["telemetry"])
        results.append({
            "case_name": tc["case_name"],
            "input_telemetry": tc["telemetry"],
            "evaluation": eval_res
        })
    return {"status": "success", "count": len(results), "test_cases": results}


# --- LEGACY STREAMLIT & BACKWARDS COMPATIBILITY ROUTES ---

@router.get("/status", tags=["Legacy Compatibility"])
def legacy_status():
    return {"status": "ONLINE", "mode": "OPERATIONAL", "agents": 7}


@router.get("/report", tags=["Legacy Compatibility"])
def legacy_report(limit: int = 10):
    return {"reports": get_latest_reports(limit=limit)}


@router.post("/input", tags=["Legacy Compatibility"])
def legacy_input(payload: Dict[str, Any]):
    return run_traffic_crew(payload)


@router.get("/alerts", tags=["Legacy Compatibility"])
def legacy_alerts(limit: int = 20):
    return {"alerts": get_all_alerts(limit=limit)}

