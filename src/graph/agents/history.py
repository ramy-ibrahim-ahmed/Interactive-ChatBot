import json
from ..state import State


async def history_node(state: State, redis_client) -> State:
    session_id = state.get("session_id")
    if not session_id:
        raise ValueError("session_id must be provided in the state for caching.")

    cache_key = f"chat_history:{session_id}"

    cached_history_str = await redis_client.lrange(cache_key, 0, 5)
    chat_history = [json.loads(msg) for msg in reversed(cached_history_str)]
    return {"history": chat_history}
