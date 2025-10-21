from enum import Enum


class ModelSizes(Enum):
    SMALL = "small"
    LARGE = "large"
    CHAT = LARGE
    CLASSIFY = SMALL
    HISTORY = SMALL
    QUERIES = LARGE
    SEMANTIC = SMALL
