from typing import List, Literal
import anyio
from fastapi import WebSocket
import pydantic
from sqlalchemy import Engine
from sqlmodel import Session, select

import clients
from clients.dto import Message
import models


class _data(pydantic.BaseModel):
    chat_id: int
    msg: str
    model: str


class Request(pydantic.BaseModel):
    type: Literal["new_message"]
    data: _data


def get_str_from_enum(
    sender: str,
) -> Literal["user", "system", "developer", "assistant"]:
    match sender:
        case "user":
            return "user"
        case "system":
            return "system"
        case "developer":
            return "developer"
        case "assistant":
            return "assistant"
        case _:
            raise ValueError("do not match with enum")


async def new_message(engine: Engine, req: Request, connections: List[WebSocket]):
    chat: models.Chat | None = None
    with Session(engine) as session:
        statement = select(models.Chat).where(models.Chat.id == req.data.chat_id)
        res = session.exec(statement)
        chat = res.first()

        if chat is None or chat.id is None:
            async with anyio.create_task_group() as tg:
                for conn in connections:
                    tg.start_soon(
                        conn.send_json,
                        {
                            "success": False,
                            "data": f"no such a chat with an id={req.data.chat_id}",
                        },
                    )
            return

        client = clients.Client()
        await client.prompt(
            [
                Message(role=get_str_from_enum(msg.sender), content=msg.contents)
                for msg in chat.messages
            ],
            req.data.msg,
            req.data.model,
        )
        llm_resp = ""
        async for chunk in client.response_stream():
            llm_resp = f"{llm_resp}{chunk.choices[0].delta.content}"
            async with anyio.create_task_group() as tg:
                for conn in connections:
                    tg.start_soon(
                        conn.send_json,
                        {"success": True, "data": chunk.to_dict()},
                    )
    with Session(engine) as session:
        session.add(
            models.Message(sender="user", contents=req.data.msg, chat_id=chat.id)
        )
        session.add(
            models.Message(sender="assistant", contents=llm_resp, chat_id=chat.id)
        )
        session.commit()
