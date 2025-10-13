from abc import ABC, abstractmethod


class BaseEmbeddings(ABC):

    @abstractmethod
    def embed(
        self, list_of_text: list[str], batch_size: int, model_name: str
    ) -> list[list[float]]: ...
