from typing import Literal
from .interface import VectorDBInterface
from .providers import QdrantProvider, PineconeProvider


class VectorDBFactory:

    def create(self, provider: Literal["qdrant"], settings) -> VectorDBInterface:
        if provider.lower() == "qdrant":
            return QdrantProvider(settings=settings)
        if provider.lower() == "pinecone":
            return PineconeProvider(settings=settings)
        else:
            raise ValueError(f"Provider {provider} is not available!")
