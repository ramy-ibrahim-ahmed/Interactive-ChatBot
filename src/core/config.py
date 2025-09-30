from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENAI_API_KEY: str
    COHERE_API_KEY: str
    VECTORDB: str
    EMBEDDING_MODEL: str
    EMBEDDING_SIZE: int
    PINECONE_API_KEY: str
    PINECONE_HOST: str
    RERANKER_MODEL: str
    GEMINI_NAME: str
    GEMINI_API_KEYS: list[str]
    PINECONE_INDEX: str
    GEMINI_API_KEY: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
