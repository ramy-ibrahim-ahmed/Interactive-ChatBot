from openai import AsyncOpenAI
from ..interfaces import BaseGenerator


class OpenAIWrapperGenerator(BaseGenerator):
    def __init__(self, client):
        self.client: AsyncOpenAI = client

    async def chat(
        self, messages: list[dict], model_name: str, temperature=0.0, top_p=1.0
    ) -> str:
        kwargs = {
            "model": model_name,
            "messages": messages,
        }
        if temperature:
            kwargs["temperature"] = temperature
            kwargs["top_p"] = top_p
        response = await self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    async def structured_chat(
        self, response_model, model_name, messages, temperature=0.0, top_p=1.0
    ):
        response = await self.client.beta.chat.completions.parse(
            model=model_name,
            messages=messages,
            response_format=response_model,
            temperature=temperature,
            top_p=top_p,
        )
        msg = response.choices[0].message
        return msg.parsed

    async def stream_chat(
        self, messages: list[dict], model_name: str, temperature=0.0, top_p=1.0
    ):
        kwargs = {
            "model": model_name,
            "messages": messages,
            "stream": True,
        }
        if temperature:
            kwargs["temperature"] = temperature
            kwargs["top_p"] = top_p

        response = await self.client.chat.completions.create(**kwargs)
        async for chunk in response:
            yield chunk.choices[0].delta.content or ""
