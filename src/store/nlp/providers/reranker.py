from ..interfaces import BaseReranker
from cohere import AsyncClientV2


class CohereReranker(BaseReranker):
    def __init__(self, cohere_client):
        self.cohere_client: AsyncClientV2 = cohere_client

    async def rerank(self, query, documents, model_name, top_n):
        response = await self.cohere_client.rerank(
            model=model_name,
            query=query,
            documents=documents,
            top_n=top_n,
        )

        return [
            {"score": item.relevance_score, "text": {documents[item.index]}}
            for item in response.results
        ]
