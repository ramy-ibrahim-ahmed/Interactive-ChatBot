import structlog
from openai import AsyncOpenAI
from ..interfaces import BaseGenerator

LOGGER = structlog.get_logger(__name__)


class OpenAIWrapperGenerator(BaseGenerator):
    def __init__(self, client, model_names):
        self.client: AsyncOpenAI = client
        self.model_names = model_names

    async def chat(
        self, messages: list[dict], model_size: str, temperature=0.0, top_p=1.0
    ) -> str:
        kwargs = {
            "model": self.model_names[model_size],
            "messages": messages,
        }
        if temperature:
            kwargs["temperature"] = temperature
            kwargs["top_p"] = top_p
        try:
            response = await self.client.chat.completions.create(**kwargs)
        except Exception as e:
            LOGGER.exception("Error during OpenAI chat request", error=str(e))
        return response.choices[0].message.content

    async def structured_chat(
        self, response_model, model_size, messages, temperature=0.0, top_p=1.0
    ):
        response = await self.client.beta.chat.completions.parse(
            model=self.model_names[model_size],
            messages=messages,
            response_format=response_model,
            temperature=temperature,
            top_p=top_p,
        )
        msg = response.choices[0].message
        return msg.parsed

    async def stream_chat(
        self, messages: list[dict], model_size: str, temperature=0.0, top_p=1.0
    ):
        kwargs = {
            "model": self.model_names[model_size],
            "messages": messages,
            "stream": True,
        }
        if temperature:
            kwargs["temperature"] = temperature
            kwargs["top_p"] = top_p

        response = await self.client.chat.completions.create(**kwargs)
        async for chunk in response:
            yield chunk.choices[0].delta.content or ""
