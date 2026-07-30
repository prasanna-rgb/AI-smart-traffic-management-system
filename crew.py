"""
CrewAI Orchestrator for Multi-Agent Smart Traffic Pipeline.
Manages sequential agent execution and database persistence.
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any

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
from database.db import (
    save_traffic_input,
    save_traffic_report,
    save_alert,
    save_analytics,
    save_driver_safety_log
)


class SmartTrafficCrew:
    """Orchestrator class for managing the 7-agent CrewAI traffic pipeline."""

    def __init__(self):
        self.llm = get_llm()

    def run(self, telemetry_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute full multi-agent traffic optimization pipeline.
        
        Args:
            telemetry_input: Dictionary with traffic metrics.
            
        Returns:
            JSON summary of all 7 agents' decisions.
        """
        road_name = telemetry_input.get("road", "Main Road")
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

        # Persist agent outputs to DB
        t_rep = report_dict["traffic_report"]
        # Persist agent outputs to DB
        t_rep = report_dict["traffic_report"]
        d_safe = report_dict.get("driver_safety", {})
        c_pred = report_dict["congestion_prediction"]
        e_corr = report_dict["emergency_corridor"]
        s_opt = report_dict["signal_optimization"]
        c_alt = report_dict["citizen_alerts"]
        a_sum = report_dict["analytics_summary"]

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
            alert_type="CITIZEN" if not e_corr.get("green_corridor_active") else "EMERGENCY",
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

        logger.info(f"Pipeline complete for {road_name}. Congestion Score: {c_pred.get('congestion_score')}, Safety Score: {d_safe.get('safety_score')}")
        return report_dict

    def _run_rule_based_flow(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """Execute high-speed deterministic workflow across all agents."""
        # 1. Traffic Monitoring Agent
        traffic_report = process_traffic_monitor_rule_based(telemetry)
        
        # 2. Driver Behavior & Safety Analytics Agent
        driver_safety = process_driver_safety_rule_based(telemetry)

        # 3. Congestion Prediction Agent
        congestion_prediction = process_congestion_rule_based(traffic_report)
        
        # 4. Emergency Vehicle Agent
        emergency_corridor = process_emergency_rule_based(traffic_report, congestion_prediction)
        
        # 5. Smart Weather Adaptability Agent
        weather_adaptation = process_weather_rule_based(traffic_report)
        
        # 6. Signal Optimization Agent (incorporates weather green time extension)
        signal_optimization = process_signal_rule_based(traffic_report, congestion_prediction, emergency_corridor)
        if weather_adaptation.get("weather_green_extension_sec", 0) > 0:
            signal_optimization["recommended_green_time_sec"] += weather_adaptation["weather_green_extension_sec"]
            signal_optimization["signal_mode"] += f"-WeatherAdapt({traffic_report.get('weather')})"
        
        # 7. Citizen Communication Agent
        citizen_alerts = process_citizen_rule_based(traffic_report, congestion_prediction, emergency_corridor)
        if weather_adaptation.get("weather_condition") in ["Rain", "Storm", "Fog"]:
            citizen_alerts["message"] += f" {weather_adaptation.get('driver_weather_warning')}"
        if driver_safety.get("risk_level") in ["CRITICAL", "HIGH"]:
            citizen_alerts["message"] += f" ⚠️ DRIVER SAFETY WARNING: {driver_safety.get('primary_hazard')}."

        # 8. Analytics Agent
        analytics_summary = process_analytics_rule_based(traffic_report, congestion_prediction, signal_optimization)

        return {
            "execution_timestamp": datetime.utcnow().isoformat(),
            "road_monitored": telemetry.get("road", "Main Road"),
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

        # Clean up any None values if CrewAI agent creation returned None
        agents = {k: v for k, v in agents.items() if v is not None}

        tasks = create_traffic_tasks(agents, telemetry)

        crew = Crew(
            agents=list(agents.values()),
            tasks=tasks,
            process=Process.sequential,
            verbose=2
        )

        crew_output = crew.kickoff()
        
        # Merge Crew execution results with fallback structure for complete fields
        base = self._run_rule_based_flow(telemetry)
        base["crew_raw_output"] = str(crew_output)
        return base



# Singleton instance helper
def run_traffic_crew(telemetry_input: Dict[str, Any]) -> Dict[str, Any]:
    orchestrator = SmartTrafficCrew()
    return orchestrator.run(telemetry_input)
