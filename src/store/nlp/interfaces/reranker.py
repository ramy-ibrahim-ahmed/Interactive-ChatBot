from abc import ABC, abstractmethod


class BaseReranker(ABC):

    @abstractmethod
    def rerank(
        self, query: str, documents: list[str], model_name: str, top_n: int
    ) -> list[dict]: ...
