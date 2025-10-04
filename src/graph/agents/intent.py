from ..state import State
from ...store.nlp import NLPInterface, PromptFactory
from ...core.enums import OpenAIRolesEnum


async def intent_node(state: State, nlp_openai: NLPInterface):
    user_message = state.get("user_message")
    intent_prompt = PromptFactory().get_prompt("user_intent")
    messages = [
        {"role": OpenAIRolesEnum.SYSTEM.value, "content": intent_prompt},
        {"role": OpenAIRolesEnum.USER.value, "content": user_message},
    ]
    intent = await nlp_openai.chat(messages, "gpt-4.1-mini", temperature=0.0, top_p=1.0)
    return {"intent": intent}
