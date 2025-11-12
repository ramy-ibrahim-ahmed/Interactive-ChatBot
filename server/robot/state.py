from typing_extensions import TypedDict
from ..core.schemas import Queries


class State(TypedDict):
    user_message: str
    intent: str
    system_name: str
    queries: Queries
    search: str
    response: str
    history: str
    route: str
