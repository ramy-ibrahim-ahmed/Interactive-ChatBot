from abc import ABC, abstractmethod
from pydantic import BaseModel


class NLPInterface(ABC):

    @abstractmethod
    def embed(
        self, list_of_text: list[str], batch_size: int, model_name: str
    ) -> list[list[float]]: ...

    @abstractmethod
    def chat(
        self,
        messages: list[dict],
        model_name: str,
        temperature: float,
        top_p: float,
    ) -> list[list[float]]: ...

    @abstractmethod
    def structured_chat(
        self,
        response_model: BaseModel,
        model_name: str,
        messages: str,
        temperature: float,
        top_p: float,
    ) -> BaseModel: ...

    @abstractmethod
    def rerank(
        self, query: str, documents: list[str], model_name: str, top_n: int
    ) -> list[str]: ...

    @abstractmethod
    def text_to_speech(self, text: str) -> str: ...

    @abstractmethod
    def speech_to_text(self, audio_path: str) -> str: ...
