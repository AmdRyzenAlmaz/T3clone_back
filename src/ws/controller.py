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
from ws import manager, new_message, create_chat

import clients
from ws.send_chats import send_existing_chats

ws_router = fastapi.APIRouter()


async def get_current_websocket_user(websocket: WebSocket) -> User:
    if websocket.client is None:
        raise WebSocketException(
            reason="NO CLIENT, MAKE A REQUEST FROM A NORMAL CLIENT",
            code=status.WS_1008_POLICY_VIOLATION,
        )
    issuer_ip = f"{websocket.client.host}"
    engine = websocket.app.state.engine
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketException(
            reason="Missing token query parameter",
            code=status.WS_1008_POLICY_VIOLATION,
        )

    try:
        payload = utils.decode_jwt(token, issuer_ip)
        if payload is None or payload.get("sub") is None:
            raise WebSocketException(
                reason="Invalid token",
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


@ws_router.websocket("/ws", dependencies=[])
async def ws_root(
    websocket: WebSocket, user: Annotated[User, Depends(get_current_websocket_user)]
):
    engine = websocket.app.state.engine
    connection_id = utils.gen_connection_id()
    if user.id is None:
        raise WebSocketException(
            reason="User not found",
            code=status.WS_1008_POLICY_VIOLATION,
        )

    await manager.on_connect(websocket, user.id, connection_id)
    await send_existing_chats(user.id, engine, manager.get_connections(user.id))
    try:
        while True:
            exception1 = None
            exception2 = None
            data = await websocket.receive_json()
            try:
                req = create_chat.Request.model_validate(data)
                await create_chat.create_new_chat(
                    engine, req, manager.get_connections(user.id), user.id
                )
                return
            except Exception as e:
                print("AAAAAAA")
                print(e)
                exception1 = WebSocketException(
                    reason="validation error",
                    code=status.WS_1002_PROTOCOL_ERROR,
                )
            try:
                req = new_message.Request.model_validate(data)
                await new_message.new_message(
                    engine, req, manager.get_connections(user.id)
                )
                return
            except Exception as e:
                print("BBBBBBB")
                print(e)
                exception2 = WebSocketException(
                    reason="validation error",
                    code=status.WS_1002_PROTOCOL_ERROR,
                )
            if exception1 is not None and exception2 is not None:
                raise exception1

    except WebSocketDisconnect:
        await manager.on_disconnect(connection_id, user.id)
