import structlog
from openai import AsyncOpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    retry_if_result,
)
from openai import (
    RateLimitError,
    APITimeoutError,
    InternalServerError,
    APIConnectionError,
)
from ..interfaces import BaseGenerator

RETRYABLE_EXCEPTIONS = (
    RateLimitError,
    APITimeoutError,
    InternalServerError,
    APIConnectionError,
)
LOGGER = structlog.get_logger(__name__)


class OpenAIWrapperGenerator(BaseGenerator):
    def __init__(self, client, model_names):
        self.client: AsyncOpenAI = client
        self.model_names = model_names

    @retry(
        retry=(
            retry_if_exception_type(RETRYABLE_EXCEPTIONS)
            | retry_if_result(lambda result: result is None)
        ),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def chat(
        self, messages: list[dict], model_size: str, temperature=0.0, top_p=1.0
    ) -> str | None:  # Updated return type hint for clarity
        kwargs = {
            "model": self.model_names[model_size],
            "messages": messages,
        }
        if temperature:
            kwargs["temperature"] = temperature
            kwargs["top_p"] = top_p
        try:
            response = await self.client.chat.completions.create(**kwargs)
            if response and response.choices:
                return response.choices[0].message.content

            LOGGER.warning("Received an empty or invalid response. Retrying...")
            return None

        except RETRYABLE_EXCEPTIONS as e:
            LOGGER.warning(
                f"Retryable error encountered: {e}. Retrying...", exc_info=True
            )
            raise e

        except Exception as e:
            LOGGER.exception("Non-retryable error during chat request", error=str(e))
            raise e

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
