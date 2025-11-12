from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENAI_API_KEY: str
    COHERE_API_KEY: str
    GEMINI_API_KEYS: list[str]
    GEMINI_API_KEY: str
    PINECONE_API_KEY: str

    PINECONE_INDEX_DENSE: str
    PINECONE_HOST_DENSE: str
    PINECONE_HOST_SPARSE: str

    EMBEDDING_MODEL: str
    EMBEDDING_SIZE: int
    SEMANTIC_TOP_K: int

    PROB_MODEL_FILE: str
    LEXICAL_TOP_K: int

    RERANKER_MODEL: str
    RERANKER_TOP_K: int

    REDIS_PORT: int
    REDIS_PASSWORD: int

    PROVIDER_EMBEDDINGS: str
    PROVIDER_RERANKER: str
    PROVIDER_STT: str
    PROVIDER_TTS: str

    GENERATOR_GEMINI_LARGE: str
    GENERATOR_GEMINI_SMALL: str
    GENERATOR_OPENAI_LARGE: str
    GENERATOR_OPENAI_SMALL: str
    GENERATOR_OLLAMA_LARGE: str
    GENERATOR_OLLAMA_SMALL: str

    @property
    def generator_config(self):
        return {
            "gemini": {
                "large": self.GENERATOR_GEMINI_LARGE,
                "small": self.GENERATOR_GEMINI_SMALL,
            },
            "openai": {
                "large": self.GENERATOR_OPENAI_LARGE,
                "small": self.GENERATOR_OPENAI_SMALL,
            },
            "ollama": {
                "large": self.GENERATOR_OLLAMA_LARGE,
                "small": self.GENERATOR_OLLAMA_SMALL,
            },
        }

    class Config:
        env_file = "./server/.env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
