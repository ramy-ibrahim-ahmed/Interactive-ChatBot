from abc import ABC, abstractmethod


class BaseEmbeddings(ABC):

    @abstractmethod
    def embed(
        self, list_of_text: list[str], model_name: str, batch_size: int
    ) -> list[list[float]]: ...
