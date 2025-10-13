from ..state import State
from ...store.nlp import NLPInterface, PromptFactory
from ...core.enums import OpenAIRolesEnum


async def intent_node(state: State, generator: NLPInterface):
    user_message = state.get("user_message")
    intent_prompt = PromptFactory().get_prompt("user_intent")
    chat_history = state.get("history")
    messages = [
        {"role": OpenAIRolesEnum.SYSTEM.value, "content": intent_prompt},
        *chat_history,
        {"role": OpenAIRolesEnum.USER.value, "content": user_message},
    ]
    intent = await generator.chat(messages, "gemini-2.5-flash", temperature=0.0, top_p=1.0)
    return {"intent": intent}
