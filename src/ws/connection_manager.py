from typing import Dict, List
from fastapi import WebSocket

from conf import get_list_of_models


class ConnectionManager:
    def __init__(self) -> None:
        self._active_connections: Dict[int, Dict[str, WebSocket]] = {}

    def get_connections(self, user_id: int) -> List[WebSocket]:
        conns = self._active_connections.get(user_id)
        if conns is None:
            return []
        return list(conns.values())

    async def on_connect(self, ws: WebSocket, user_id: int, conn_id: str):
        await ws.accept()
        await ws.send_json(get_list_of_models())
        if self._active_connections.get(user_id) is None:
            self._active_connections[user_id] = {conn_id: ws}

    async def on_disconnect(self, conn_id: str, user_id: int):
        if self._active_connections.get(user_id) is not None:
            ws = self._active_connections[user_id].pop(conn_id)
            await ws.close()


manager = ConnectionManager()
