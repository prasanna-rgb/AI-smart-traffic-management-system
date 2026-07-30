"""
Pydantic Data Schemas for API Requests, Responses, and Agent Data Models.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TrafficInputSchema(BaseModel):
    """Input payload for incoming traffic telemetry."""
    road: str = Field(..., example="Main Road")
    vehicle_count: int = Field(..., ge=0, example=82)
    average_speed: float = Field(..., ge=0.0, example=31.0)
    road_occupancy_pct: float = Field(default=75.0, ge=0.0, le=100.0, example=78.5)
    accident: bool = Field(default=False, example=False)
    emergency_vehicle: bool = Field(default=True, example=True)
    emergency_type: Optional[str] = Field(default="Ambulance", example="Ambulance")
    weather: str = Field(default="Rain", example="Rain")


class TrafficReportSchema(BaseModel):
    """Traffic Monitoring Agent Output Schema."""
    road: str
    vehicles: int
    density: str
    average_speed: float
    accident: bool
    emergency_vehicle: bool
    emergency_type: Optional[str] = None
    weather: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class CongestionPredictionSchema(BaseModel):
    """Congestion Prediction Agent Output Schema."""
    road: str
    congestion_score: float
    risk_level: str
    predicted_trend: str
    estimated_delay_minutes: float
    recommended_alternate_roads: List[str]


class EmergencyCorridorSchema(BaseModel):
    """Emergency Vehicle Agent Output Schema."""
    emergency_detected: bool
    vehicle_type: Optional[str]
    green_corridor_active: bool
    corridor_route: List[str]
    signal_override_status: str
    priority_level: str


class SignalOptimizationSchema(BaseModel):
    """Signal Optimization Agent Output Schema."""
    junction: str
    current_green_time_sec: int
    recommended_green_time_sec: int
    dynamic_increase_sec: int
    estimated_wait_time_reduction_pct: float
    signal_mode: str


class CitizenAlertSchema(BaseModel):
    """Citizen Communication Agent Output Schema."""
    alert_id: str
    timestamp: str
    title: str
    severity: str
    message: str
    affected_road: str
    alternate_route: Optional[str] = None
    broadcast_channels: List[str]


class AnalyticsReportSchema(BaseModel):
    """Analytics Agent Output Schema."""
    timestamp: str
    road_name: str
    vehicle_count: int
    average_speed: float
    congestion_level: str
    carbon_emission_kg: float
    road_performance_score: float
    key_insights: List[str]


class SystemStatusSchema(BaseModel):
    """System Health and Operational Status Schema."""
    status: str
    version: str
    active_agents: int
    junctions_monitored: int
    active_emergency_corridors: int
    database_status: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class CrewExecutionOutputSchema(BaseModel):
    """Combined JSON Output of full CrewAI execution flow."""
    execution_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    road_monitored: str
    traffic_report: Dict[str, Any]
    congestion_prediction: Dict[str, Any]
    emergency_corridor: Dict[str, Any]
    signal_optimization: Dict[str, Any]
    citizen_alerts: Dict[str, Any]
    analytics_summary: Dict[str, Any]
