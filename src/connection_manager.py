from typing import Dict
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._active_connections: Dict[str, WebSocket] = {}

    async def on_connect(self, ws: WebSocket, conn_id: str):
        self._active_connections[conn_id] = ws

    def on_disconnect(self, connection_id: str):
        self._active_connections.pop(connection_id)
