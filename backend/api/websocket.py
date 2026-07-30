"""
WebSocket Manager for Broadcasting Real-time Telemetry, Frames, and Decision Logs.
"""
import json
import asyncio
import logging
from typing import List, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("smart_traffic_ai.api.ws")


class ConnectionManager:
    """Manages active WebSocket dashboard subscriptions."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket Client Connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket Client Disconnected. Remaining connections: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast JSON payload to all connected frontend clients."""
        if not self.active_connections:
            return

        dead_connections = []
        payload = json.dumps(message)
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception as e:
                logger.warning(f"Error broadcasting to WS client: {e}")
                dead_connections.append(connection)

        for conn in dead_connections:
            self.disconnect(conn)


ws_manager = ConnectionManager()
