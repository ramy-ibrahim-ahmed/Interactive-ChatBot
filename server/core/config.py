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

    GENERATOR_LARGE: str
    GENERATOR_SMALL: str

    REDIS_PORT: int
    REDIS_PASSWORD: int

    class Config:
        env_file = "./server/.env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
