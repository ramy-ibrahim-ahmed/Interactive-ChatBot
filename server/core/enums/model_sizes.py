from enum import Enum

SMALL = "small"
LARGE = "large"


class ModelSizes(Enum):
    CHAT = LARGE
    CLASSIFY = SMALL
    HISTORY = LARGE
    QUERIES = LARGE
    SEMANTIC = LARGE
