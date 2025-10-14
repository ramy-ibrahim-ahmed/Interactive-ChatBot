from typing import Literal, Optional
from openai import AsyncOpenAI
from cohere import AsyncClientV2
from .providers.embeddings import OpenAIEmbeddings, CohereEmbeddings
from .providers.generator import OpenAIWrapperGenerator
from .providers.reranker import CohereReranker
from .providers.stt import OpenAISTT
from .providers.tts import OpenAITTS
from ...core.config import get_settings

SETTINGS = get_settings()


def _init_openai_wrapper(api_key: str, base_url: Optional[str] = None):
    if base_url:
        return AsyncOpenAI(api_key=api_key, base_url=base_url)
    return AsyncOpenAI(api_key=api_key)


def _init_cohere_client(api_key: str):
    return AsyncClientV2(api_key=api_key)


class NLPFactory:

    @staticmethod
    def create_embeddings(provider: Literal["openai", "cohere"]):
        if provider.lower() == "openai":
            openai_client = _init_openai_wrapper(SETTINGS.OPENAI_API_KEY)
            return OpenAIEmbeddings(openai_client=openai_client)
        elif provider.lower() == "cohere":
            cohere_client = _init_cohere_client(SETTINGS.COHERE_API_KEY)
            return CohereEmbeddings(cohere_client=cohere_client)
        else:
            raise ValueError("Non-valid provider!")

    @staticmethod
    def create_generator(provider: Literal["openai", "gemini", "ollama"]):
        if provider.lower() == "openai":
            openai_client = _init_openai_wrapper(SETTINGS.OPENAI_API_KEY)
            return OpenAIWrapperGenerator(client=openai_client)
        elif provider.lower() == "gemini":
            gemini_client = _init_openai_wrapper(
                api_key=SETTINGS.GEMINI_API_KEY,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            )
            return OpenAIWrapperGenerator(client=gemini_client)
        elif provider.lower() == "ollama":
            ollama_client = _init_openai_wrapper(
                api_key="ollama", base_url="http://localhost:11434/v1"
            )
            return OpenAIWrapperGenerator(client=ollama_client)
        else:
            raise ValueError("Non-valid provider!")

    @staticmethod
    def create_reranker(provider: Literal["cohere"]):
        if provider.lower() == "cohere":
            cohere_client = _init_cohere_client(SETTINGS.COHERE_API_KEY)
            return CohereReranker(cohere_client=cohere_client)
        else:
            raise ValueError("Non-valid provider!")

    @staticmethod
    def create_stt(provider: Literal["openai"]):
        if provider.lower() == "openai":
            openai_client = _init_openai_wrapper(SETTINGS.OPENAI_API_KEY)
            return OpenAISTT(openai_client=openai_client)
        else:
            raise ValueError("Non-valid provider!")

    @staticmethod
    def create_tts(provider: Literal["openai"]):
        if provider.lower() == "openai":
            openai_client = _init_openai_wrapper(SETTINGS.OPENAI_API_KEY)
            return OpenAITTS(openai_client=openai_client)
        else:
            raise ValueError("Non-valid provider!")
