from typing import List
import openai

from clients import dto
from conf import get_api_key, get_llm_endpoint
from utils import SingletonMeta


class Client(metaclass=SingletonMeta):
    def __init__(self) -> None:
        api_key = get_api_key()
        endpoint = get_llm_endpoint()
        self.client = openai.AsyncClient(api_key=api_key, base_url=endpoint)

    async def prompt(
        self,
        chat_history: List[dto.Message],
        message_content: str,
        model: str,
    ):
        new_msg = dto.Message(role="user", content=message_content)
        messages = [*chat_history, new_msg]
        self.response = await self.client.chat.completions.create(
            stream=True,
            model=model,
            messages=messages,
        )

    async def response_stream(self):
        async for chunk in self.response:
            yield chunk
