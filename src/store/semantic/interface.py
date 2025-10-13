from abc import ABC, abstractmethod
from typing import List, Dict


class VectorDBInterface(ABC):
    @abstractmethod
    async def connect(self) -> None: ...

    @abstractmethod
    async def disconnect(self) -> None: ...

    @abstractmethod
    async def is_exists(self, name: str) -> bool: ...

    @abstractmethod
    async def create_collection(self, name: str) -> None: ...

    @abstractmethod
    async def delete_collection(self, name: str) -> None: ...

    @abstractmethod
    async def upsert(
        self,
        vectors: List[List[float]],
        metadata: List[Dict],
        collection_name: str,
        batch_size: int,
    ) -> None: ...

    @abstractmethod
    async def query_chunks(
        self, vectors: List[List[float]], collection_name: str, max_retrieved: int
    ) -> List[Dict]: ...
