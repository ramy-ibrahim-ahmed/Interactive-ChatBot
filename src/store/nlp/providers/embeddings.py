import numpy as np
from openai import AsyncOpenAI
from ..interfaces import BaseEmbeddings


def normalize_embeddings(vectors: list[list[float]]):
    return [
        (vec / np.linalg.norm(vec)) if np.linalg.norm(vec) != 0 else vec
        for vec in vectors
    ]


class OpenAIEmbeddings(BaseEmbeddings):
    def __init__(self, openai_client):
        self.openai_client: AsyncOpenAI = openai_client

    async def embed(
        self,
        list_of_text: list[str],
        batch_size=10,
        model_name="text-embedding-3-large",
    ) -> list[list[float]]:

        vectors = []
        for i in range(0, len(list_of_text), batch_size):
            batch = list_of_text[i : i + batch_size]
            response = await self.openai_client.embeddings.create(
                input=batch, model=model_name
            )
            batch_vectors = [item.embedding for item in response.data]
            normalized = normalize_embeddings(batch_vectors)
            vectors.extend(normalized)

        return vectors


class CohereEmbeddings(BaseEmbeddings):
    def __init__(self, cohere_client):
        self.cohere_client = cohere_client

    async def embed(
        self,
        list_of_text: list[str],
        batch_size=10,
        model_name="embed-v4.0",
    ) -> list[list[float]]:

        vectors = []
        for i in range(0, len(list_of_text), batch_size):
            batch = list_of_text[i : i + batch_size]
            response = await self.cohere_client.embed(
                texts=batch,
                model=model_name,
                input_type="search_document",
                embedding_types=["float"],
                output_dimension=1024,
            )
            batch_vectors = response.embeddings.float
            normalized = normalize_embeddings(batch_vectors)
            vectors.extend(normalized)

        return vectors
