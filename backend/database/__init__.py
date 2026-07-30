# Database package initialization
from .models import Base, TrafficDataDB, TrafficReportDB, AlertDB, AnalyticsDB
from .db import (
    init_db,
    get_db,
    save_traffic_input,
    save_traffic_report,
    save_alert,
    save_analytics,
    get_latest_traffic_data,
    get_latest_reports,
    get_active_alerts,
    get_analytics_summary
)

__all__ = [
    "Base",
    "TrafficDataDB",
    "TrafficReportDB",
    "AlertDB",
    "AnalyticsDB",
    "init_db",
    "get_db",
    "save_traffic_input",
    "save_traffic_report",
    "save_alert",
    "save_analytics",
    "get_latest_traffic_data",
    "get_latest_reports",
    "get_active_alerts",
    "get_analytics_summary"
]
