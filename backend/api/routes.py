"""
FastAPI REST API Router for Smart Traffic Management System (Backend Package).
Exposes live traffic telemetry, multi-agent pipeline execution, report retrieval, and developer debug endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from models.schemas import (
    TrafficInputSchema,
    TrafficReportSchema,
    SystemStatusSchema,
    CrewExecutionOutputSchema
)
from database.db import (
    get_latest_reports,
    get_latest_traffic_data,
    get_active_alerts,
    get_analytics_summary,
    save_driver_safety_log,
    get_driver_safety_logs
)
from tools.traffic_data_fetcher import TrafficDataFetcher, get_data_lineage
from tools.driver_behavior_tools import DriverBehaviorTools
from crew import run_traffic_crew

router = APIRouter(prefix="/traffic", tags=["Traffic Management"])


@router.get("/status", response_model=SystemStatusSchema)
def get_system_status():
    """Get operational status of the AI Traffic System and database connection."""
    reports = get_latest_reports(limit=10)
    active_corridors = sum(1 for r in reports if r.get("green_corridor_active"))
    
    return SystemStatusSchema(
        status="ONLINE",
        version="1.0.0",
        active_agents=7,
        junctions_monitored=5,
        active_emergency_corridors=active_corridors,
        database_status="CONNECTED"
    )


@router.get("/live")
def get_live_traffic_data(road_name: str = Query("Main Road", description="Target road or junction name")):
    """
    Fetch structured real-time traffic data (validated metrics) from data fetcher engine.
    """
    try:
        data = TrafficDataFetcher.get_traffic_data(road_name=road_name)
        return {
            "status": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch live traffic data: {str(e)}")


@router.post("/refresh")
def refresh_traffic_pipeline(road_name: str = Query("Main Road", description="Target road or junction name")):
    """
    Force-refresh traffic data fetcher and execute multi-agent CrewAI decision pipeline.
    """
    try:
        traffic_data = TrafficDataFetcher.get_traffic_data(road_name=road_name)
        pipeline_output = run_traffic_crew(traffic_data)
        return {
            "status": "success",
            "message": f"Traffic data refreshed & pipeline executed for {road_name}",
            "live_data": traffic_data,
            "pipeline_report": pipeline_output
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh traffic pipeline: {str(e)}")


@router.get("/debug/data-lineage")
def get_debug_data_lineage(road_name: str = Query("Main Road", description="Target road or junction name")):
    """
    Developer debug endpoint returning 5-stage data lineage flow:
    DATA SOURCE -> RAW RESPONSE -> NORMALIZED RESPONSE -> TRAFFIC AGENT INPUT -> TRAFFIC AGENT OUTPUT
    """
    try:
        reports = get_latest_reports(limit=10)
        filtered = [r for r in reports if r.get("road_name") == road_name]
        latest_agent_output = filtered[0].get("full_report") if filtered else None
        lineage = get_data_lineage(road_name=road_name, agent_output=latest_agent_output)
        return lineage
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate data lineage trace: {str(e)}")


@router.post("/input", response_model=CrewExecutionOutputSchema)
def process_traffic_input(payload: Optional[TrafficInputSchema] = None, simulate: bool = Query(False, description="If True, auto-generate synthetic telemetry")):
    """
    Accept custom traffic telemetry data or trigger simulation tick, then execute CrewAI multi-agent pipeline.
    """
    if simulate or payload is None:
        telemetry = TrafficDataFetcher.get_traffic_data("Main Road")
    else:
        telemetry = payload.model_dump()

    try:
        report_output = run_traffic_crew(telemetry)
        return report_output
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process traffic agent pipeline: {str(e)}")


@router.get("/report")
def get_traffic_reports(limit: int = Query(10, ge=1, le=50)):
    """Fetch latest traffic reports and agent execution decisions."""
    reports = get_latest_reports(limit=limit)
    if not reports:
        sim_data = TrafficDataFetcher.get_traffic_data("Main Road")
        run_traffic_crew(sim_data)
        reports = get_latest_reports(limit=limit)
    return {"count": len(reports), "reports": reports}


@router.get("/analytics")
def get_traffic_analytics(limit: int = Query(20, ge=1, le=100)):
    """Fetch historical traffic analytics, carbon emission statistics, and performance scores."""
    analytics = get_analytics_summary(limit=limit)
    alerts = get_active_alerts(limit=limit)
    raw_data = get_latest_traffic_data(limit=limit)
    
    return {
        "count": len(analytics),
        "analytics": analytics,
        "recent_alerts": alerts,
        "raw_telemetry": raw_data
    }


@router.post("/driver-safety/analyze")
def analyze_driver_safety(telemetry: Dict[str, Any]):
    """
    Analyze driver telemetry to detect violations, compute Safety Score (0-100),
    predict risk probability, and generate safety alerts.
    """
    try:
        result = DriverBehaviorTools.evaluate_telemetry(telemetry)
        save_driver_safety_log(result)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze driver behavior: {str(e)}")


@router.get("/driver-safety/logs")
def fetch_driver_safety_logs(limit: int = Query(20, ge=1, le=100)):
    """Retrieve persisted driver safety logs."""
    logs = get_driver_safety_logs(limit=limit)
    return {"count": len(logs), "logs": logs}


@router.get("/driver-safety/test-cases")
def get_driver_safety_test_cases():
    """Returns 6 predefined telemetry test cases for demonstration and testing."""
    test_cases = DriverBehaviorTools.get_test_cases()
    results = []
    for tc in test_cases:
        eval_res = DriverBehaviorTools.evaluate_telemetry(tc["telemetry"])
        results.append({
            "case_name": tc["case_name"],
            "input_telemetry": tc["telemetry"],
            "evaluation": eval_res
        })
    return {"count": len(results), "test_cases": results}
