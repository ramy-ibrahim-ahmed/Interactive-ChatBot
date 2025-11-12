from abc import ABC, abstractmethod
from pydantic import BaseModel


class BaseGenerator(ABC):

    @abstractmethod
    def chat(
        self,
        messages: list[dict],
        model_size: str,
        temperature: float,
        top_p: float,
    ) -> str: ...

    @abstractmethod
    async def stream_chat(
        self, messages: list[dict], model_size: str, temperature=0.0, top_p=1.0
    ): ...

    @abstractmethod
    def structured_chat(
        self,
        response_model: BaseModel,
        model_size: str,
        messages: str,
        temperature: float,
        top_p: float,
    ) -> BaseModel: ...
