import structlog
from typing import Literal
from langgraph.types import Command
from ..state import State
from ...store.nlp import PromptFactory
from ...store.nlp.interfaces import BaseGenerator
from ...core.enums import OpenAIRolesEnum
from ...core.schemas import Decision
from ...core.config import get_settings

LOGGER = structlog.getLogger(__name__)
SETTINGS = get_settings()


async def SemanticAgent(
    state: State, generator: BaseGenerator
) -> Command[Literal["__classify__", "__end__"]]:

    user_message = state.get("user_message")
    instructions = PromptFactory().get_prompt("semantic")
    history = state.get("history")

    messages = [
        {"role": OpenAIRolesEnum.SYSTEM.value, "content": instructions},
        {"role": OpenAIRolesEnum.ASSISTANT.value, "content": history},
        {"role": OpenAIRolesEnum.USER.value, "content": user_message},
    ]

    decision: Decision = await generator.structured_chat(
        Decision, SETTINGS.GENERATOR_SMALL, messages
    )

    LOGGER.info(f"Routed --> {decision.decision}", agent="Semantic")

    return Command(goto=decision.decision)
