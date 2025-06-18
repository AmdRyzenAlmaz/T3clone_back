from typing import List
import anyio
from fastapi import WebSocket
from sqlalchemy import Engine
from sqlmodel import Session, select
from models import Chat, Message


async def send_existing_chats(
    user_id: int, engine: Engine, connections: List[WebSocket]
):
    with Session(engine) as session:
        stmt = select(Chat).where(Chat.user_id == user_id)
        res = session.exec(stmt)
        chats = list(map(lambda x: x.model_dump(), res.all()))
        for chat in chats:
            stm = select(Message).where(Message.chat_id == chat["id"])
            rs = session.exec(stm)
            chat["messages"] = list(map(lambda x: x.model_dump(), rs.all()))

        async with anyio.create_task_group() as tg:
            for conn in connections:
                tg.start_soon(
                    conn.send_json,
                    {"success": True, "data": chats},
                )
