from ..state import State
from ...store.nlp import NLPInterface, PromptFactory
from ...core.enums import OpenAIRolesEnum
from ...core.schemas.guide import SearchQueries


async def query_node(state: State, generator: NLPInterface) -> State:
    prompt_query = PromptFactory().get_prompt("query_write")
    user_message = state.get("user_message")
    chat_history = state.get("history")
    messages = [
        {"role": OpenAIRolesEnum.SYSTEM.value, "content": prompt_query},
        *chat_history,
        {"role": OpenAIRolesEnum.USER.value, "content": user_message},
    ]
    enhanced_query = await generator.structured_chat(
        SearchQueries, "gemini-2.5-flash", messages
    )
    return {"enhanced_query": enhanced_query}
