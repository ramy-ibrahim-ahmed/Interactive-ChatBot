import structlog
from ..state import State
from ...store.nlp import PromptFactory
from ...core.enums import OpenAIRolesEnum
from ...core.config import get_settings

SETTINGS = get_settings()
LOGGER = structlog.getLogger(__name__)


async def ChatAgent(state: State, generator):
    instructions = PromptFactory().get_prompt("chat")
    user_message = state.get("user_message")
    search = state.get("search", "No Search")
    history = state.get("history")

    chat_history = "Chat History: " + history
    retrieved = "Retrieved Context:\n\n" + search

    messages = [
        {"role": OpenAIRolesEnum.SYSTEM.value, "content": instructions},
        {"role": OpenAIRolesEnum.ASSISTANT.value, "content": chat_history},
        {"role": OpenAIRolesEnum.ASSISTANT.value, "content": retrieved},
        {"role": OpenAIRolesEnum.USER.value, "content": user_message},
    ]

    LOGGER.info("Streaming response...", agent="Chat")

    full_response = ""

    async for chunk in generator.stream_chat(messages, SETTINGS.GENERATOR_LARGE):
        if chunk:
            yield {"chunk": chunk}
            full_response += chunk

    yield {"event": "complete", "response": full_response}
