from fastapi import WebSocket, WebSocketDisconnect
import fastapi
import utils
from conf import manager

ws_router = fastapi.APIRouter()


@ws_router.websocket("/ws")
async def ws_root(websocket: WebSocket):
    connection_id = utils.gen_connection_id()
    await manager.on_connect(websocket, connection_id)
    try:
        while True:
            data = await websocket.receive_text()
            print(data)
    except WebSocketDisconnect:
        manager.on_disconnect(connection_id)
