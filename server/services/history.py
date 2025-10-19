import redis.asyncio as redis
from typing import List, Dict, Any, Optional
from ..store.nlp.interfaces.generator import BaseGenerator
from ..core.config import get_settings
from ..core.enums import ModelSizes

SETTINGS = get_settings()


class ChatHistoryServie:
    _CACHE_KEY_PREFIX = "chat_summary"

    def __init__(self, cachedb: redis.Redis, generator: BaseGenerator):
        self.cachedb = cachedb
        self.generator = generator

    def _get_cache_key(self, session_id: str) -> str:
        return f"{self._CACHE_KEY_PREFIX}:{session_id}"

    async def get_summary(self, session_id: str) -> Optional[str]:
        cache_key = self._get_cache_key(session_id)
        summary_str = await self.cachedb.get(cache_key)

        if summary_str:
            return summary_str

        return None

    async def update_summary(self, session_id: str, messages: List[Dict[str, Any]]):
        new_summary = await self.generator.chat(messages, ModelSizes.HISTORY.value)
        cache_key = self._get_cache_key(session_id)
        await self.cachedb.set(cache_key, new_summary)

    async def delete_summary(self, session_id: str) -> int:
        cache_key = self._get_cache_key(session_id)
        await self.cachedb.delete(cache_key)
