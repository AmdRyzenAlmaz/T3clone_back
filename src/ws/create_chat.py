from typing import List, Literal
import anyio
from fastapi import WebSocket
import pydantic
from sqlalchemy import Engine
from sqlmodel import Session

import clients
from clients.dto import Message
from conf import SYSTEM_PROMPT
from models import Chat
import models


class _data(pydantic.BaseModel):
    msg: str
    model: str


class Request(pydantic.BaseModel):
    type: Literal["new_chat"]
    data: _data


async def create_new_chat(
    engine: Engine, req: Request, connections: List[WebSocket], user_id: int
) -> None:
    client = clients.Client()
    await client.prompt(
        [Message(role="system", content=SYSTEM_PROMPT)],
        req.data.msg,
        req.data.model,
    )
    llm_resp = ""
    async for chunk in client.response_stream():
        llm_resp = f"{llm_resp}{chunk.choices[0].delta.content}"
        try:
            async with anyio.create_task_group() as tg:
                for conn in connections:
                    tg.start_soon(
                        conn.send_json, {"success": True, "data": chunk.to_dict()}
                    )
        except ExceptionGroup as eg:
            print(f"Caught exception group: {eg}")
            for exc in eg.exceptions:
                print(f"Sub-exception: {exc}")

    with Session(engine) as session:
        chat = Chat(
            chat_name=req.data.msg,
            user_id=user_id,
        )
        session.add(chat)
        session.commit()
        session.add(
            models.Message(sender="system", contents=SYSTEM_PROMPT, chat_id=chat.id)
        )
        session.add(
            models.Message(sender="user", contents=req.data.msg, chat_id=chat.id)
        )
        session.add(
            models.Message(sender="assistant", contents=llm_resp, chat_id=chat.id)
        )
        session.commit()

        try:
            async with anyio.create_task_group() as tg:
                for conn in connections:
                    tg.start_soon(
                        conn.send_json, {"success": True, "data": {"chat_id": chat.id}}
                    )
        except ExceptionGroup as eg:
            print(f"Caught exception group: {eg}")
            for exc in eg.exceptions:
                print(f"Sub-exception: {exc}")
