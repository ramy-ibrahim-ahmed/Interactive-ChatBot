from ..state import State
from ...store.nlp import NLPInterface, PromptFactory
from ...core.enums import OpenAIRolesEnum
from ...core.schemas.guide import SearchQueries


async def query_node(state: State, nlp_openai: NLPInterface) -> State:
    prompt_query = PromptFactory().get_prompt("query_write")
    user_message = state.get("user_message")
    chat_history = state.get("history")
    messages = [
        {"role": OpenAIRolesEnum.SYSTEM.value, "content": prompt_query},
        # *chat_history,
        {"role": OpenAIRolesEnum.USER.value, "content": user_message},
    ]
    enhanced_query = await nlp_openai.structured_chat(
        SearchQueries, "gpt-4.1", messages
    )
    return {"enhanced_query": enhanced_query}
