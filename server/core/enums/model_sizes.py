from enum import Enum


class ModelSizes(Enum):
    SMALL = "small"
    LARGE = "large"
    CHAT = SMALL
    CLASSIFY = SMALL
    HISTORY = SMALL
    QUERIES = SMALL
    SEMANTIC = SMALL
    OCR = LARGE
    POST_OCR = SMALL
    CHUNK = SMALL
