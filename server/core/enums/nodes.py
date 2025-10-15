from enum import Enum


class NodesEnum(Enum):
    SEMANTIC_ROUTER = "__semantic__"
    CLASSIFY = "__classify__"
    QUERIES = "__queries__"
    SEARCH = "__search__"
    CHAT = "__chat__"
    TTS = "__tts__"
    STT = "__stt__"
