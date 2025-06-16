from typing import Literal
import pydantic


class Message(pydantic.BaseModel):
    role: (
        Literal["user"]
        | Literal["system"]
        | Literal["developer"]
        | Literal["assistant"]
    )
    content: str
