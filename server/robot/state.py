from typing_extensions import TypedDict
from ..core.schemas.search import ManySearchResults, SearchQueries


class State(TypedDict):
    user_message: str
    intent: str
    system_name: str
    queries: SearchQueries
    search_obj: ManySearchResults
    search_str: str
    response: str
    history: str
