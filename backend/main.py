"""
Main FastAPI Server Entry Point for Agentic AI Smart Traffic Management System.
Features REST APIs, WebSockets, OpenCV/YOLOv8 vision stream worker, 6 CrewAI Agents, and PostgreSQL database.
"""
import sys
import asyncio
import threading
import time
import logging
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from config.settings import APP_NAME, VERSION, API_HOST, API_PORT, DEBUG
from database.db import init_db, SessionLocal, get_all_intersections
from api.routes import router as traffic_router
from api.websocket import ws_manager
from vision.stream_processor import stream_processor
from crew import run_traffic_crew

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("smart_traffic_ai.main")

# Initialize Database Schema
init_db()

app = FastAPI(
    title=APP_NAME,
    version=VERSION,
    description="Production-Ready Agentic AI Smart Traffic Management System using Python, CrewAI, FastAPI, React, PostgreSQL, YOLOv8, and OpenCV.",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for React Frontend and external clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Router
app.include_router(traffic_router)


# WebSocket Streaming Endpoint
@app.websocket("/ws/traffic")
async def websocket_traffic_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection open & handle incoming client messages
            data = await websocket.receive_text()
            logger.debug(f"Received WS message: {data}")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket connection error: {e}")
        ws_manager.disconnect(websocket)


# Background Telemetry Broadcast Loop
def background_telemetry_loop(loop):
    """Background thread emitting live 10Hz frames and signal ticks via WebSocket."""
    logger.info("Starting Background Telemetry & Frame Streaming Loop...")
    stream_processor.start_stream("synthetic")

    tick = 0
    while True:
        try:
            stream_data = stream_processor.get_latest_data()
            metrics = stream_data.get("metrics", {})
            frame_b64 = stream_data.get("frame_b64", "")

            tick += 1

            # Run 6-agent CrewAI pipeline periodically (every ~5 seconds)
            if tick % 50 == 0 and metrics:
                try:
                    telemetry_payload = {
                        "intersection_code": metrics.get("intersection_code", "INT-01"),
                        "car": metrics.get("car", 12),
                        "bus": metrics.get("bus", 2),
                        "truck": metrics.get("truck", 1),
                        "motorcycle": metrics.get("motorcycle", 4),
                        "ambulance": metrics.get("ambulance", 0),
                        "total_vehicles": metrics.get("total_vehicles", 19),
                        "average_speed": metrics.get("average_speed", 38.0),
                        "emergency_vehicle": metrics.get("ambulance", 0) > 0
                    }
                    run_traffic_crew(telemetry_payload)
                except Exception as ex:
                    logger.error(f"Error in automatic background crew execution: {ex}")

            # Fetch updated intersections
            db = SessionLocal()
            try:
                intersections = get_all_intersections(db)
            finally:
                db.close()

            broadcast_payload = {
                "type": "TELEMETRY_UPDATE",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "frame_b64": frame_b64,
                "metrics": metrics,
                "intersections": intersections
            }

            asyncio.run_coroutine_threadsafe(ws_manager.broadcast(broadcast_payload), loop)
        except Exception as err:
            logger.error(f"Error in background telemetry stream: {err}")

        time.sleep(0.1)


@app.on_event("startup")
def startup_event():
    """Startup tasks: seed initial data and spawn background telemetry worker thread."""
    logger.info(f"[{APP_NAME}] Startup sequence initiated.")
    
    # Run initial seed crew run
    try:
        seed_payload = {"intersection_code": "INT-01", "vehicles": 25, "average_speed": 42.0, "emergency_vehicle": False}
        run_traffic_crew(seed_payload)
        logger.info("[Startup] Seed crew execution completed.")
    except Exception as e:
        logger.warning(f"[Startup] Seed crew warning: {e}")

    # Start asyncio background loop thread
    main_loop = asyncio.get_event_loop()
    thread = threading.Thread(target=background_telemetry_loop, args=(main_loop,), daemon=True)
    thread.start()


@app.get("/")
def root_endpoint():
    return {
        "app": APP_NAME,
        "version": VERSION,
        "status": "ONLINE",
        "vision_engine": "OpenCV + YOLOv8",
        "agents": [
            "Vision Agent",
            "Traffic Analysis Agent",
            "Prediction Agent",
            "Pollution Agent",
            "Emergency Agent",
            "Decision Agent"
        ],
        "docs": "/docs",
        "websocket": "/ws/traffic"
    }


if __name__ == "__main__":
    logger.info(f"Starting FastAPI Server on http://{API_HOST}:{API_PORT}")
    uvicorn.run("main:app", host=API_HOST, port=API_PORT, reload=DEBUG)
