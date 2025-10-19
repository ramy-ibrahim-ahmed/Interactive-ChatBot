import structlog
from ..state import State
from ...store.nlp import PromptFactory
from ...store.nlp.interfaces import BaseGenerator
from ...core.enums import OpenAIRolesEnum, ModelSizes
from ...core.schemas import Queries
from ...core.config import get_settings

SETTINGS = get_settings()
LOGGER = structlog.get_logger(__name__)


async def QueriesAgent(state: State, generator: BaseGenerator) -> State:

    instructions = PromptFactory().get_prompt("queries")
    user_message = state.get("user_message")
    history = state.get("history")

    chat_history = "Chat History: " + history
    messages = [
        {"role": OpenAIRolesEnum.SYSTEM.value, "content": instructions},
        {"role": OpenAIRolesEnum.ASSISTANT.value, "content": chat_history},
        {"role": OpenAIRolesEnum.USER.value, "content": user_message},
    ]

    queries: Queries = await generator.structured_chat(
        Queries, ModelSizes.QUERIES.value, messages
    )

    LOGGER.info(
        f"Fusion: {len(queries.semantic_queries)}, Lexical: {1 if queries.lexical_search_query else 0}, Cross Encoder: {1 if queries.reranker_query else 0}",
        agent="Queries",
    )

    return {"queries": queries}
