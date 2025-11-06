from enum import Enum


class ModelSizes(Enum):
    SMALL = "small"
    LARGE = "large"
    CHAT = LARGE
    CLASSIFY = LARGE
    HISTORY = LARGE
    QUERIES = LARGE
    SEMANTIC = LARGE
    OCR = LARGE
    POST_OCR = SMALL
    CHUNK = SMALL
