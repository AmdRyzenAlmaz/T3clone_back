from typing import Annotated, List
from fastapi import (
    Depends,
    WebSocket,
    WebSocketDisconnect,
    status,
    WebSocketException,
)
import fastapi
import pydantic
from auth import get_user_by_id
from models import User
import utils
from ws import manager

import clients

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

        user = get_user_by_id(engine, payload["sub"])
        if not user:
            raise WebSocketException(
                reason="User not found",
                code=status.WS_1008_POLICY_VIOLATION,
            )

        return user
    except Exception as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketException(reason=str(e), code=status.WS_1008_POLICY_VIOLATION)


class Request(pydantic.BaseModel):
    type: str
    chat_history: List[clients.Message]
    message: str


@ws_router.websocket("/ws", dependencies=[])
async def ws_root(
    websocket: WebSocket, user: Annotated[User, Depends(get_current_websocket_user)]
):
    connection_id = utils.gen_connection_id()
    await manager.on_connect(websocket, connection_id)
    clietn = clients.Client()
    try:
        while True:
            data = await websocket.receive_json()
            req = Request.model_validate(data)
            await clietn.prompt(req.chat_history, req.message)
            async for chunk in clietn.response_stream():
                await websocket.send_json(chunk.to_dict())

    except WebSocketDisconnect:
        manager.on_disconnect(connection_id)
