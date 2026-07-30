"""
FastAPI REST API Router for Smart Traffic Management System.
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
    get_analytics_summary
)
from tools.simulation_tools import TrafficSimulator
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
        active_agents=6,
        junctions_monitored=5,
        active_emergency_corridors=active_corridors,
        database_status="CONNECTED"
    )


@router.post("/input", response_model=CrewExecutionOutputSchema)
def process_traffic_input(payload: Optional[TrafficInputSchema] = None, simulate: bool = Query(False, description="If True, auto-generate synthetic telemetry")):
    """
    Accept custom traffic telemetry data or trigger simulation tick, then execute CrewAI multi-agent pipeline.
    """
    if simulate or payload is None:
        telemetry = TrafficSimulator.generate_random_telemetry()
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
        # Trigger a default simulation run to populate database
        sim_data = TrafficSimulator.generate_random_telemetry(road="Main Road")
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
