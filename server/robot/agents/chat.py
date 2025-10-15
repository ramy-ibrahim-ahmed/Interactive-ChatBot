import structlog
from ..state import State
from ...store.nlp import PromptFactory
from ...core.enums import OpenAIRolesEnum
from ...core.config import get_settings

SETTINGS = get_settings()
LOGGER = structlog.getLogger(__name__)


async def chat_node(state: State, generator):

    instructions = PromptFactory().get_prompt("chat")
    user_message = state.get("user_message")
    search = state.get("search")
    history = state.get("history")

    messages = [
        {"role": OpenAIRolesEnum.SYSTEM.value, "content": instructions},
        {"role": OpenAIRolesEnum.ASSISTANT.value, "content": history},
        {"role": OpenAIRolesEnum.ASSISTANT.value, "content": search},
        {"role": OpenAIRolesEnum.USER.value, "content": user_message},
    ]

    LOGGER.info("Streaming response...", agent="Chat")

    state["response"] = ""
    async for chunk in generator.stream_chat(messages, SETTINGS.GENERATOR_LARGE):
        state["response"] += chunk
        yield {"chunk": chunk}
