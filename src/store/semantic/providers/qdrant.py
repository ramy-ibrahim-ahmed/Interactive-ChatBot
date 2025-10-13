from qdrant_client import QdrantClient, models
from ..interface import VectorDBInterface


class QdrantProvider(VectorDBInterface):
    def __init__(self, settings):
        self.qdrant_client = None

    def connect(self) -> None:
        self.qdrant_client = QdrantClient(
            host="qdrant", grpc_port=6334, prefer_grpc=True
        )

    def disconnect(self) -> None:
        if self.qdrant_client:
            self.qdrant_client.close()

    def is_exists(self, name: str) -> bool:
        return self.qdrant_client.collection_exists(name)

    def create_collection(self, name: str, embedding_size) -> None:
        self.qdrant_client.create_collection(
            collection_name=name,
            vectors_config=models.VectorParams(
                size=embedding_size, distance=models.Distance.COSINE
            ),
        )

    def delete_collection(self, name: str) -> None:
        self.qdrant_client.delete_collection(name)

    def upsert(self, vectors, metadata, collection_name, batch_size=100):
        points = [
            models.PointStruct(id=i, vector=embedding, payload=payload)
            for i, (embedding, payload) in enumerate(zip(vectors, metadata), start=1)
        ]

        self.qdrant_client.upsert(
            collection_name=collection_name,
            points=points,
            wait=True,
        )

    def query_chunks(self, vectors, collection_name, max_retrieved):
        nearest = self.qdrant_client.query_batch_points(
            collection_name=collection_name,
            requests=[
                models.QueryRequest(query=e, with_payload=True, limit=max_retrieved)
                for e in vectors
            ],
        )
        all_payloads = [point.payload for result in nearest for point in result.points]
        return [
            dict(item_tuple)
            for item_tuple in set(tuple(sorted(d.items())) for d in all_payloads)
        ]
