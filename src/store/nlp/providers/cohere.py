from ..interface import NLPInterface


class CohereProvider(NLPInterface):
    def __init__(self, cohere_client):
        self.cohere_client = cohere_client

    def rerank(self, query, documents, model_name, top_n):
        response = self.cohere_client.rerank(
            model=model_name,
            query=query,
            documents=documents,
            top_n=top_n,
        )

        sorted_results = sorted(
            response.results, key=lambda x: x.relevance_score, reverse=True
        )[:top_n]

        ranked = []
        for item in sorted_results:
            ranked.append(
                {
                    "index": item.index,
                    "score": float(item.relevance_score),
                    "topic": documents[item.index]["topic_id"],
                    "text": documents[item.index]["text"],
                }
            )

        return ranked

    def embed(self, list_of_text, batch_size, model_name): ...
    def chat(self, messages, model_name): ...
    def structured_chat(self, response_model, model_name, messages): ...
    def text_to_speech(self, text: str) -> str: ...
    def speech_to_text(self, audio_path: str) -> str: ...
