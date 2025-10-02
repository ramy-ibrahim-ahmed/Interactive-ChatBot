import numpy as np
from ..interface import NLPInterface


class CohereProvider(NLPInterface):
    def __init__(self, cohere_client):
        self.cohere_client = cohere_client

    def rerank(self, query, documents, model_name, top_n):
        response = self.cohere_client.rerank(
            model=model_name,
            query=query,
            documents=[doc["text"] for doc in documents],
            top_n=top_n,
        )

        sorted_results = sorted(
            response.results, key=lambda x: x.relevance_score, reverse=True
        )[:top_n]

        ranked = []
        for item in sorted_results:
            doc = documents[item.index]
            ranked.append(
                {
                    "index": item.index,
                    "score": float(item.relevance_score),
                    "topic": doc["topic_id"],
                    "text": doc["text"],
                }
            )

        return ranked

    def embed(
        self,
        list_of_text: list[str],
        batch_size=10,
        model_name="embed-v4.0",
    ) -> list[list[float]]:
        vectors = []
        for i in range(0, len(list_of_text), batch_size):
            batch = list_of_text[i : i + batch_size]
            response = self.cohere_client.embed(
                texts=batch,
                model=model_name,
                input_type="search_document",
                embedding_types=["float"],
                output_dimension=1024,
            )
            batch_vectors = response.embeddings.float
            batch_vectors = [
                (vec / np.linalg.norm(vec)) if np.linalg.norm(vec) != 0 else vec
                for vec in batch_vectors
            ]
            vectors.extend(batch_vectors)
        return vectors

    def chat(self, messages, model_name, temperature, top_p): ...
    def structured_chat(
        self, response_model, model_name, messages, temperature, top_p
    ): ...
    def text_to_speech(self, text: str) -> str: ...
    def speech_to_text(self, audio_path: str) -> str: ...
