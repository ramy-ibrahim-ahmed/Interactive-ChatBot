import numpy as np
from ..interface import NLPInterface


class OpenAIProvider(NLPInterface):
    def __init__(self, openai_client):
        self.openai_client = openai_client

    def embed(self, list_of_text, batch_size=1, model_name="text-embedding-3-large"):
        vectors = []
        for i in range(0, len(list_of_text), batch_size):
            batch = list_of_text[i : i + batch_size]
            response = self.openai_client.embeddings.create(
                input=batch, model=model_name
            )
            batch_vectors = [item.embedding for item in response.data]
            batch_vectors = [
                (vec / np.linalg.norm(vec)) if np.linalg.norm(vec) != 0 else vec
                for vec in batch_vectors
            ]
            vectors.extend(batch_vectors)
        return vectors

    def chat(self, messages: list[dict], model_name: str) -> list[list[float]]:
        # response = self.openai_client.beta.chat.completions.parse(
        #     model=model_name, messages=messages, temperature=0.0, top_p=1.0
        # )
        response = self.openai_client.beta.chat.completions.parse(
            model=model_name, messages=messages
        )
        return response.choices[0].message.content

    def structured_chat(self, response_model, model_name, messages):
        response = self.openai_client.beta.chat.completions.parse(
            model=model_name,
            messages=messages,
            response_format=response_model,
            temperature=0.0,
            top_p=1.0,
        )
        msg = response.choices[0].message
        return msg.parsed

    def rerank(self, query, documents, model_name): ...
