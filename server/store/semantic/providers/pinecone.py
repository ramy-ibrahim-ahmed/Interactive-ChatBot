from uuid import uuid4
from pinecone import Pinecone, ServerlessSpec, Vector
from ..interface import VectorDBInterface


class PineconeProvider(VectorDBInterface):
    def __init__(self, settings):
        self.settings = settings
        self.client = None
        self.index = None

    def connect(self):
        self.client = Pinecone(api_key=self.settings.PINECONE_API_KEY)
        index_name = self.settings.PINECONE_INDEX_DENSE
        if index_name not in self.client.list_indexes().names():
            self.client.create_index(
                name=index_name,
                dimension=self.settings.EMBEDDING_SIZE,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )

        self.index = self.client.Index(index_name)

    def disconnect(self):
        if self.index:
            self.index.close()

    def is_exists(self, name: str) -> bool:
        return name in self.index.list_namespaces()

    def create_collection(self, name: str):
        return True

    def delete_collection(self, name: str) -> bool:
        try:
            self.index.delete(namespace=name)
            return True
        except Exception as e:
            print(f"Delete failed: {e}")
            return False

    def upsert(self, vectors, metadata, collection_name, batch_size=100):
        vectors_metadata = [
            Vector(id=str(uuid4()), values=vectors[i].tolist(), metadata=metadata[i])
            for i in range(len(vectors))
        ]
        try:
            self.index.upsert(
                vectors=vectors_metadata,
                namespace=collection_name,
                batch_size=batch_size,
                show_progress=False,
            )
            return True
        except Exception as e:
            print(f"Upsert failed: {e}")
            return False

    def query_chunks(self, vectors, collection_name, max_retrieved):
        matches = []
        for vec in vectors:
            response = self.index.query(
                namespace=collection_name,
                vector=vec.tolist(),
                top_k=max_retrieved,
                include_metadata=True,
                include_values=False,
            )
            matches.extend([m.metadata for m in response.matches])
        return matches
