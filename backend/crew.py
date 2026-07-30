"""
CrewAI Orchestrator for Multi-Agent Smart Traffic Pipeline (Backend Package).
Manages sequential agent execution, emergency response workflow, automatic recovery, and database persistence.
"""
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

try:
    from crewai import Crew, Process
    CREWAI_AVAILABLE = True
except Exception as e:
    CREWAI_AVAILABLE = False
    Crew = None
    Process = None

from config.settings import get_llm
from agents.traffic_monitor import create_traffic_monitor_agent, process_traffic_monitor_rule_based
from agents.congestion_agent import create_congestion_agent, process_congestion_rule_based
from agents.emergency_agent import create_emergency_agent, process_emergency_rule_based
from agents.signal_agent import create_signal_agent, process_signal_rule_based
from agents.citizen_agent import create_citizen_agent, process_citizen_rule_based
from agents.analytics_agent import create_analytics_agent, process_analytics_rule_based
from agents.driver_safety_agent import create_driver_safety_agent, process_driver_safety_rule_based
from agents.weather_agent import create_weather_agent, process_weather_rule_based
from tools.audio_announcer import get_emergency_voice_script
from database.db import (
    save_traffic_input,
    save_traffic_report,
    save_alert,
    save_analytics,
    save_driver_safety_log,
    save_emergency_event
)

logger = logging.getLogger("smart_traffic_ai.crew")


class SmartTrafficCrew:
    """Orchestrator class for managing the multi-agent traffic pipeline and emergency workflow."""

    def __init__(self):
        self.llm = get_llm()

    def run(self, telemetry_input: Dict[str, Any], registered_phone: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute full multi-agent traffic optimization & emergency response pipeline.
        """
        if registered_phone and isinstance(telemetry_input, dict):
            telemetry_input["registered_phone"] = registered_phone
        road_name = telemetry_input.get("road_name", telemetry_input.get("road", "Main Road"))
        logger.info(f"Starting Multi-Agent Traffic Pipeline for: {road_name}")

        # Persist raw telemetry
        save_traffic_input(telemetry_input)

        # Execute agents sequentially
        if self.llm is not None:
            try:
                report_dict = self._run_crewai_agent_flow(telemetry_input)
            except Exception as e:
                logger.warning(f"CrewAI LLM execution encountered exception: {e}. Falling back to Rule-Based Engine.")
                report_dict = self._run_rule_based_flow(telemetry_input)
        else:
            logger.info("Using Rule-Based Engine (No Gemini API key or LLM fallback).")
            report_dict = self._run_rule_based_flow(telemetry_input)

        # Extract agent responses
        t_rep = report_dict["traffic_report"]
        d_safe = report_dict.get("driver_safety", {})
        c_pred = report_dict["congestion_prediction"]
        e_corr = report_dict["emergency_corridor"]
        s_opt = report_dict["signal_optimization"]
        c_alt = report_dict["citizen_alerts"]
        a_sum = report_dict["analytics_summary"]

        # 🚨 Handle Emergency Event Persistence & Recovery Logging
        has_emergency = e_corr.get("emergency_detected", False) or t_rep.get("accident_status", False)
        is_recovery = telemetry_input.get("accident_resolved", False) and telemetry_input.get("emergency_vehicle_passed", False)

        if has_emergency or is_recovery:
            evt_type = "RESOLVED" if is_recovery else e_corr.get("event_type", "ACCIDENT")
            evt_severity = "NORMAL" if is_recovery else e_corr.get("severity", "CRITICAL")
            evt_status = "RESOLVED" if is_recovery else "ACTIVE"
            v_type = e_corr.get("vehicle_type", "AMBULANCE")

            save_emergency_event({
                "event_id": f"EVT-{uuid.uuid4().hex[:6].upper()}",
                "event_type": evt_type,
                "severity": evt_severity,
                "road_name": road_name,
                "location": {
                    "latitude": t_rep.get("location", {}).get("latitude", 13.0827),
                    "longitude": t_rep.get("location", {}).get("longitude", 80.2707)
                },
                "emergency_vehicle_type": v_type,
                "signal_before": s_opt.get("signal_before_display", "Green 30s / Red 30s"),
                "signal_after": s_opt.get("signal_after_display", "Green 50s / Red 15s"),
                "green_time_before": s_opt.get("current_green_time_sec", 30),
                "green_time_after": s_opt.get("recommended_green_time_sec", 50),
                "voice_alert_sent": True,
                "citizen_alert_sent": True,
                "status": evt_status
            })

        if d_safe:
            try:
                save_driver_safety_log(d_safe)
            except Exception as d_err:
                logger.warning(f"Failed to persist driver safety log: {d_err}")

        save_traffic_report(
            road_name=road_name,
            density=t_rep.get("density", "Medium"),
            congestion_score=c_pred.get("congestion_score", 40.0),
            signal_mode=s_opt.get("signal_mode", "Standard"),
            green_corridor=e_corr.get("green_corridor_active", False),
            report_dict=report_dict
        )

        save_alert(
            alert_type="EMERGENCY" if has_emergency else "CITIZEN",
            severity=c_alt.get("severity", "INFO"),
            title=c_alt.get("title", "Traffic Update"),
            message=c_alt.get("message", ""),
            road_name=road_name,
            alternate_route=c_alt.get("alternate_route")
        )

        save_analytics(
            road_name=road_name,
            vehicles=t_rep.get("vehicles", 50),
            avg_speed=t_rep.get("average_speed", 40.0),
            congestion_index=c_pred.get("congestion_score", 40.0),
            carbon_kg=a_sum.get("carbon_emission_kg", 15.0),
            performance=a_sum.get("road_performance_score", 75.0),
            notes="; ".join(a_sum.get("key_insights", []))
        )

        logger.info(f"Pipeline complete for {road_name}. Congestion: {c_pred.get('congestion_score')}, Emergency: {has_emergency}")
        return report_dict

    def _run_rule_based_flow(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """Execute high-speed deterministic workflow across all agents."""
        # Check Automatic Recovery condition
        is_recovery = telemetry.get("accident_resolved", False) and telemetry.get("emergency_vehicle_passed", False)
        
        if is_recovery:
            telemetry["accident"] = False
            telemetry["accident_status"] = False
            telemetry["emergency_vehicle"] = False
            telemetry["emergency_vehicle_status"] = False

        # 1. Traffic Monitoring Agent
        traffic_report = process_traffic_monitor_rule_based(telemetry)
        
        # 2. Driver Behavior & Safety Analytics Agent
        driver_safety = process_driver_safety_rule_based(telemetry)

        # 3. Congestion Prediction Agent
        congestion_prediction = process_congestion_rule_based(traffic_report)
        
        # 4. Emergency Vehicle Agent
        emergency_corridor = process_emergency_rule_based(traffic_report, congestion_prediction)
        
        if is_recovery:
            emergency_corridor["emergency_detected"] = False
            emergency_corridor["green_corridor_active"] = False
            emergency_corridor["event_type"] = "NORMAL"
            emergency_corridor["severity"] = "NORMAL"
            emergency_corridor["priority_level"] = "NORMAL"
            emergency_corridor["signal_override_status"] = "INACTIVE: Emergency Resolved. Adaptive Traffic Signals Restored."

        # 5. Smart Weather Adaptability Agent
        weather_adaptation = process_weather_rule_based(traffic_report)
        
        # 6. Signal Optimization Agent
        signal_optimization = process_signal_rule_based(traffic_report, congestion_prediction, emergency_corridor)
        if weather_adaptation.get("weather_green_extension_sec", 0) > 0:
            signal_optimization["recommended_green_time_sec"] += weather_adaptation["weather_green_extension_sec"]
            signal_optimization["signal_mode"] += f"-WeatherAdapt({traffic_report.get('weather')})"
        
        if is_recovery:
            signal_optimization["recommended_green_time_sec"] = 30
            signal_optimization["recommended_yellow_time_sec"] = 5
            signal_optimization["recommended_red_time_sec"] = 30
            signal_optimization["dynamic_increase_sec"] = 0
            signal_optimization["signal_mode"] = "STANDARD ADAPTIVE BALANCED (Restored)"
            signal_optimization["signal_after_display"] = "🟢 Green: 30s | 🟡 Yellow: 5s | 🔴 Red: 30s"
            if "ai_explanation" not in signal_optimization or not isinstance(signal_optimization["ai_explanation"], dict):
                signal_optimization["ai_explanation"] = {}
            signal_optimization["ai_explanation"]["reason"] = "Emergency situation resolved. Normal adaptive signal timing restored."

        # 7. Citizen Communication Agent
        citizen_alerts = process_citizen_rule_based(traffic_report, congestion_prediction, emergency_corridor)
        if is_recovery:
            citizen_alerts["title"] = f"✅ EMERGENCY RESOLVED - {telemetry.get('road', 'Main Road').upper()}"
            citizen_alerts["severity"] = "INFO"
            citizen_alerts["message"] = f"The emergency situation on {telemetry.get('road', 'Main Road')} has been resolved. Normal traffic operations are being restored."
            citizen_alerts["alternate_route"] = None

        # Generate Voice AI Emergency Script
        voice_script = get_emergency_voice_script(
            road_name=telemetry.get('road_name', telemetry.get('road', 'Main Road')),
            event_type=emergency_corridor.get('event_type', 'NORMAL'),
            vehicle_type=emergency_corridor.get('vehicle_type', 'AMBULANCE'),
            lane_name=emergency_corridor.get('affected_lane', 'Lane 1 (Emergency Priority Corridor)'),
            resolved=is_recovery
        )
        emergency_corridor["voice_script"] = voice_script

        # 8. Analytics Agent
        analytics_summary = process_analytics_rule_based(traffic_report, congestion_prediction, signal_optimization)

        return {
            "execution_timestamp": datetime.utcnow().isoformat(),
            "road_monitored": telemetry.get("road_name", telemetry.get("road", "Main Road")),
            "traffic_report": traffic_report,
            "driver_safety": driver_safety,
            "congestion_prediction": congestion_prediction,
            "emergency_corridor": emergency_corridor,
            "weather_adaptation": weather_adaptation,
            "signal_optimization": signal_optimization,
            "citizen_alerts": citizen_alerts,
            "analytics_summary": analytics_summary
        }

    def _run_crewai_agent_flow(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """Execute CrewAI multi-agent sequential pipeline."""
        agents = {
            "monitor": create_traffic_monitor_agent(),
            "driver_safety": create_driver_safety_agent(),
            "congestion": create_congestion_agent(),
            "emergency": create_emergency_agent(),
            "signal": create_signal_agent(),
            "citizen": create_citizen_agent(),
            "analytics": create_analytics_agent()
        }

        agents = {k: v for k, v in agents.items() if v is not None}
        tasks = create_traffic_tasks(agents, telemetry)

        crew = Crew(
            agents=list(agents.values()),
            tasks=tasks,
            process=Process.sequential,
            verbose=2
        )

        crew_output = crew.kickoff()
        base = self._run_rule_based_flow(telemetry)
        base["crew_raw_output"] = str(crew_output)
        return base


def run_traffic_crew(telemetry_input: Dict[str, Any], registered_phone: Optional[str] = None) -> Dict[str, Any]:
    orchestrator = SmartTrafficCrew()
    return orchestrator.run(telemetry_input, registered_phone=registered_phone)
