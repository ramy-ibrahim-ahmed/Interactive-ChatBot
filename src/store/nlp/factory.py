from typing import Literal
from openai import AsyncOpenAI
from cohere import ClientV2
from .interface import NLPInterface
from .providers import OpenAIProvider, CohereProvider
from ...core.config import get_settings


class NLPFactory:
    def create(provider: Literal["openai", "gemini", "cohere"]) -> NLPInterface:
        if provider.lower() == "openai":
            openai_client = AsyncOpenAI(api_key=get_settings().OPENAI_API_KEY)
            return OpenAIProvider(openai_client=openai_client)
        elif provider.lower() == "gemini":
            openai_client = AsyncOpenAI(
                api_key=get_settings().GEMINI_API_KEY,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            )
            return OpenAIProvider(openai_client=openai_client)
        elif provider.lower() == "ollama":
            openai_client = AsyncOpenAI(
                api_key="ollama",
                base_url="http://localhost:11434/v1",
            )
            return OpenAIProvider(openai_client=openai_client)

        elif provider.lower() == "cohere":
            cohere_client = ClientV2(api_key=get_settings().COHERE_API_KEY)
            return CohereProvider(cohere_client=cohere_client)

        else:
            raise ValueError(f"Provider {provider} is not available!")
