from abc import ABC, abstractmethod


class BaseSTT(ABC):

    @abstractmethod
    def speech_to_text(self, audio_path: str) -> str: ...
