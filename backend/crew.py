"""
CrewAI Orchestrator for 6-Agent Smart Traffic Pipeline.
Coordinates Vision, Traffic Analysis, Prediction, Pollution, Emergency, and Decision agents.
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
from agents import (
    create_vision_agent, process_vision_rule_based,
    create_traffic_analysis_agent, process_traffic_analysis_rule_based,
    create_prediction_agent, process_prediction_rule_based,
    create_pollution_agent, process_pollution_rule_based,
    create_emergency_agent, process_emergency_rule_based,
    create_decision_agent, process_decision_rule_based
)
from tasks.traffic_tasks import create_traffic_tasks
from database.db import (
    SessionLocal,
    save_vision_metric,
    save_prediction,
    save_pollution_log,
    save_emergency_event,
    save_decision_log,
    update_intersection_signal,
    save_traffic_input,
    save_traffic_report,
    save_alert,
    save_analytics
)

logger = logging.getLogger("smart_traffic_ai.crew")


class SmartTrafficCrew:
    """Orchestrator class for managing the 6-agent CrewAI traffic pipeline."""

    def __init__(self):
        self.llm = get_llm()

    def run(self, telemetry_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute full 6-agent traffic optimization pipeline."""
        code = telemetry_input.get("intersection_code", telemetry_input.get("road", "INT-01"))
        logger.info(f"Executing 6-Agent CrewAI Traffic Optimization Pipeline for: {code}")

        save_traffic_input(telemetry_input)

        if self.llm is not None and CREWAI_AVAILABLE:
            try:
                report = self._run_crewai_agent_flow(telemetry_input)
            except Exception as e:
                logger.warning(f"CrewAI LLM execution exception ({e}). Utilizing deterministic agent reasoning engine.")
                report = self._run_rule_based_flow(telemetry_input)
        else:
            report = self._run_rule_based_flow(telemetry_input)

        # Persist all 6 agent outputs to PostgreSQL DB
        db = SessionLocal()
        try:
            save_vision_metric(db, report["vision"])
            save_prediction(db, report["prediction"])
            save_pollution_log(db, report["pollution"])
            save_emergency_event(db, report["emergency"])
            save_decision_log(db, report["decision"])

            # Update live signal state
            dec = report["decision"]
            splits = dec.get("recommended_splits", {})
            update_intersection_signal(
                db,
                code=code,
                mode=dec.get("signal_mode", "AI_AUTO"),
                phase=dec.get("active_phase", "NORTH_SOUTH_GREEN"),
                ns_timer=splits.get("north_south_green_sec", 45),
                ew_timer=splits.get("east_west_green_sec", 25)
            )

            # Persist backwards compatible reports
            vis = report["vision"]
            pred = report["prediction"]
            emg = report["emergency"]
            save_traffic_report(
                road_name=code,
                density=vis.get("density_category", "Medium"),
                congestion_score=vis.get("density_pct", 40.0),
                signal_mode=dec.get("signal_mode", "AI_AUTO"),
                green_corridor=emg.get("green_corridor_active", False),
                report_dict=report
            )
        except Exception as err:
            logger.error(f"Error persisting agent outputs to DB: {err}")
        finally:
            db.close()

        return report

    def _run_rule_based_flow(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """Execute high-speed deterministic workflow across all 6 agents."""
        vision_out = process_vision_rule_based(telemetry)
        analysis_out = process_traffic_analysis_rule_based(vision_out)
        prediction_out = process_prediction_rule_based(vision_out, analysis_out)
        pollution_out = process_pollution_rule_based(vision_out, analysis_out)
        emergency_out = process_emergency_rule_based(vision_out, analysis_out)
        decision_out = process_decision_rule_based(vision_out, analysis_out, prediction_out, pollution_out, emergency_out)

        return {
            "execution_timestamp": datetime.utcnow().isoformat(),
            "intersection_code": vision_out.get("intersection_code", "INT-01"),
            "vision": vision_out,
            "analysis": analysis_out,
            "prediction": prediction_out,
            "pollution": pollution_out,
            "emergency": emergency_out,
            "decision": decision_out
        }

    def _run_crewai_agent_flow(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """Execute CrewAI multi-agent sequential pipeline."""
        agents = {
            "vision": create_vision_agent(),
            "traffic_analysis": create_traffic_analysis_agent(),
            "prediction": create_prediction_agent(),
            "pollution": create_pollution_agent(),
            "emergency": create_emergency_agent(),
            "decision": create_decision_agent()
        }

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


def run_traffic_crew(telemetry_input: Dict[str, Any]) -> Dict[str, Any]:
    orchestrator = SmartTrafficCrew()
    return orchestrator.run(telemetry_input)
