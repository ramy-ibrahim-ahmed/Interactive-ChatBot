from ..state import State
from ...store.nlp import PromptFactory
from ...store.nlp.interfaces import BaseGenerator
from ...core.enums import OpenAIRolesEnum
from ...core.config import get_settings

SETTINGS = get_settings()


async def intent_node(state: State, generator: BaseGenerator):
    user_message = state.get("user_message")
    intent_prompt = PromptFactory().get_prompt("user_intent")
    chat_history = state.get("history")
    messages = [
        {"role": OpenAIRolesEnum.SYSTEM.value, "content": intent_prompt},
        *chat_history,
        {"role": OpenAIRolesEnum.USER.value, "content": user_message},
    ]
    intent = await generator.chat(messages, SETTINGS.GENERATOR_SMALL)
    return {"intent": intent}
