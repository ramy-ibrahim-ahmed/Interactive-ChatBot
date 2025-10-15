from ..state import State
from ...store.nlp import PromptFactory
from ...store.nlp.interfaces import BaseGenerator
from ...core.enums import OpenAIRolesEnum
from ...core.schemas.guide import SearchQueries
from ...core.config import get_settings

SETTINGS = get_settings()


async def query_node(state: State, generator: BaseGenerator) -> State:
    prompt_query = PromptFactory().get_prompt("query_write")
    user_message = state.get("user_message")
    chat_history = state.get("history")
    messages = [
        {"role": OpenAIRolesEnum.SYSTEM.value, "content": prompt_query},
        *chat_history,
        {"role": OpenAIRolesEnum.USER.value, "content": user_message},
    ]
    enhanced_query = await generator.structured_chat(
        SearchQueries, SETTINGS.GENERATOR_SMALL, messages
    )
    return {"enhanced_query": enhanced_query}
