from typing_extensions import TypedDict
from ..core.schemas.guide import ManySearchResults, SearchQueries


class State(TypedDict):
    user_message: str
    audio_path: str
    system_name: str
    enhanced_query: SearchQueries
    search_results: ManySearchResults
    formated_search: str
    response: str
    intent: str
    analysis: str
    session_id: str
    history: list[dict]
