"""
Main FastAPI Server Entry Point.
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import APP_NAME, VERSION, API_HOST, API_PORT, DEBUG
from database.db import init_db, get_latest_reports
from api.routes import router as traffic_router
from tools.simulation_tools import TrafficSimulator
from crew import run_traffic_crew

# Initialize Database Schema
init_db()

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan handler: Seed initial simulation data if database is empty."""
    reports = get_latest_reports(limit=1)
    if not reports:
        print("[Startup] Seeding initial traffic telemetry and agent decisions...")
        sample_roads = ["Main Road", "Broadway Ave", "Express Highway"]
        for road in sample_roads:
            telemetry = TrafficSimulator.generate_random_telemetry(road=road)
            run_traffic_crew(telemetry)
        print("[Startup] Initial database seeding completed.")
    yield

app = FastAPI(
    title=APP_NAME,
    version=VERSION,
    description="Multi-Agent AI Smart Traffic Management System using CrewAI, FastAPI, and Streamlit.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Enable CORS for Streamlit UI or Web Clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Router
app.include_router(traffic_router)


@app.get("/")
def root_endpoint():
    """Root status endpoint."""
    return {
        "app": APP_NAME,
        "version": VERSION,
        "status": "ONLINE",
        "documentation": "/docs",
        "endpoints": {
            "system_status": "/traffic/status",
            "traffic_report": "/traffic/report",
            "process_input": "/traffic/input",
            "analytics": "/traffic/analytics"
        }
    }


if __name__ == "__main__":
    import os
    port = int(os.getenv("API_PORT", 8000))
    host = os.getenv("API_HOST", "127.0.0.1")
    uvicorn.run("main:app", host=host, port=port, reload=DEBUG)
