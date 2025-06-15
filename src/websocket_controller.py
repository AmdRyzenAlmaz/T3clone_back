from typing import Annotated
from fastapi import (
    Depends,
    WebSocket,
    WebSocketDisconnect,
    status,
    WebSocketException,
)
import fastapi
from auth import repository
from models import User
import utils
from conf import manager

ws_router = fastapi.APIRouter()


async def get_current_websocket_user(websocket: WebSocket) -> User:
    engine = websocket.app.state.engine
    authorization = websocket.headers.get("authorization")
    if not authorization or not authorization.startswith("Bearer "):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketException(
            reason="Missing or invalid Authorization header",
            code=status.WS_1008_POLICY_VIOLATION,
        )

    token = authorization.replace("Bearer ", "")
    try:
        payload = utils.decode_jwt(token)
        if payload is None or payload.get("sub") is None:
            raise WebSocketException(
                reason="Invalid Authorization header",
                code=status.WS_1008_POLICY_VIOLATION,
            )

        user = repository.get_user_by_id(engine, payload["sub"])
        if not user:
            raise WebSocketException(
                reason="User not found",
                code=status.WS_1008_POLICY_VIOLATION,
            )

        return user
    except Exception as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketException(reason=str(e), code=status.WS_1008_POLICY_VIOLATION)


@ws_router.websocket("/ws", dependencies=[])
async def ws_root(
    websocket: WebSocket, user: Annotated[User, Depends(get_current_websocket_user)]
):
    connection_id = utils.gen_connection_id()
    await manager.on_connect(websocket, connection_id)
    try:
        while True:
            data = await websocket.receive_text()
            print(data)
    except WebSocketDisconnect:
        manager.on_disconnect(connection_id)
