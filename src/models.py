from sqlmodel import Field, Relationship, SQLModel
from pydantic import EmailStr


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True)
    email: EmailStr = Field(unique=True)
    password: str

    chats: list["Chat"] = Relationship(back_populates="user")


class Chat(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    chat_name: str | None

    user_id: int | None = Field(default=None, foreign_key="user.id")
    user: list[User] = Relationship(back_populates="chats")
    messages: list["Message"] = Relationship(back_populates="chat")


class Message(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    sender: str
    contents: str

    chat_id: int | None = Field(default=None, foreign_key="chat.id")
    chat: Chat = Relationship(back_populates="messages")
