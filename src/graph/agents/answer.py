import json
from ..state import State
from ...store.nlp import PromptFactory
from ...core.enums import OpenAIRolesEnum


async def chat_node(state: State, nlp_openai, redis_client):
    session_id = state.get("session_id")
    if not session_id:
        raise ValueError("session_id must be provided in the state for caching.")

    cache_key = f"chat_history:{session_id}"

    answer_prompt = PromptFactory().get_prompt("answer-one-step")
    user_message = state.get("user_message")
    formated_search = state.get("formated_search")

    cached_history_str = await redis_client.lrange(cache_key, 0, 5)
    chat_history = [json.loads(msg) for msg in reversed(cached_history_str)]

    messages = [{"role": OpenAIRolesEnum.SYSTEM.value, "content": answer_prompt}]
    messages.extend(chat_history)
    messages.extend(
        [
            {"role": OpenAIRolesEnum.ASSISTANT.value, "content": formated_search},
            {"role": OpenAIRolesEnum.USER.value, "content": user_message},
        ]
    )

    model_name = "gpt-4.1"
    state["response"] = ""
    async for chunk in nlp_openai.stream_chat(messages, model_name):
        state["response"] += chunk
        yield {"chunk": chunk}

    new_user_message_dict = {
        "role": OpenAIRolesEnum.USER.value,
        "content": user_message,
    }
    new_assistant_response_dict = {
        "role": OpenAIRolesEnum.ASSISTANT.value,
        "content": state["response"],
    }

    await redis_client.lpush(cache_key, json.dumps(new_assistant_response_dict))
    await redis_client.lpush(cache_key, json.dumps(new_user_message_dict))
    await redis_client.ltrim(cache_key, 0, 5)
