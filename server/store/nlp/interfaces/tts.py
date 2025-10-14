from abc import ABC, abstractmethod


class BaseTTS(ABC):

    @abstractmethod
    def text_to_speech(self, text: str) -> str: ...
