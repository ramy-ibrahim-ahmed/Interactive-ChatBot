from typing import Literal
from openai import OpenAI
from cohere import ClientV2
from .interface import NLPInterface
from .providers import OpenAIProvider, CohereProvider
from ...core.config import get_settings


class NLPFactory:
    def create(provider: Literal["openai", "cohere"]) -> NLPInterface:
        if provider.lower() == "openai":
            openai_client = OpenAI(api_key=get_settings().OPENAI_API_KEY)
            return OpenAIProvider(openai_client=openai_client)

        elif provider.lower() == "cohere":
            cohere_client = ClientV2(api_key=get_settings().COHERE_API_KEY)
            return CohereProvider(cohere_client=cohere_client)

        else:
            raise ValueError(f"Provider {provider} is not available!")
