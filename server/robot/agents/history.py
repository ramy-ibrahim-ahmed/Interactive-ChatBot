# import json
# from ..state import State
# import redis.asyncio as redis


# class ChatHistory:
#     def __init__(self, client: redis.Redis):
#         self.client = client

#     async def get_history(self, session_id):
#         cache_key = f"chat_history:{session_id}"
#         cached_history_str = await self.client.lrange(cache_key, 0)
#         return cached_history_str
    
#     async def summarize_history()

# async def history_node(state: State, cachedb) -> State:
#     session_id = state.get("session_id")
#     if not session_id:
#         raise ValueError("session_id must be provided in the state for caching.")

#     chat_history = [json.loads(msg) for msg in reversed(cached_history_str)]
#     return {"history": chat_history}

#     # new_user_message_dict = {
#     #     "role": OpenAIRolesEnum.USER.value,
#     #     "content": user_message,
#     # }
#     # new_assistant_response_dict = {
#     #     "role": OpenAIRolesEnum.ASSISTANT.value,
#     #     "content": state["response"],
#     # }

#     # await cachedb.lpush(cache_key, json.dumps(new_assistant_response_dict))
#     # await cachedb.lpush(cache_key, json.dumps(new_user_message_dict))
#     # await cachedb.ltrim(cache_key, 0, 5)

#     # LOGGER.info("We are here to create the answer", agent="Answer")

#     # session_id = state.get("session_id")
#     # if not session_id:
#     #     raise ValueError("session_id must be provided in the state for caching.")

#     # cache_key = f"chat_history:{session_id}"
