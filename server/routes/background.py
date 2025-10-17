import os
import time
from ..services import ChatHistoryServie
from ..core.enums import OpenAIRolesEnum
from ..store.nlp import PromptFactory


async def update_chat_history_task(
    session_id: str,
    user_message: str,
    search: str,
    ai_response: str,
    cachedb,
    generator,
):
    try:
        history_service = ChatHistoryServie(cachedb=cachedb, generator=generator)

        instructions = PromptFactory().get_prompt("history")
        previous_summary = await history_service.get_summary(session_id) or ""
        retrieved = "Retrieved Context:\n\n" + search
        old_history = "Chat History: " + previous_summary

        messages = [
            {"role": OpenAIRolesEnum.SYSTEM.value, "content": instructions},
            {"role": OpenAIRolesEnum.ASSISTANT.value, "content": old_history},
            {"role": OpenAIRolesEnum.USER.value, "content": user_message},
            {"role": OpenAIRolesEnum.ASSISTANT.value, "content": retrieved},
            {"role": OpenAIRolesEnum.ASSISTANT.value, "content": ai_response},
        ]

        await history_service.update_summary(session_id, messages)

    except Exception as e:
        print(f"Error in background history update for session {session_id}: {e}")


def cleanup_file_task(path: str):
    try:
        time.sleep(60)
        os.remove(path)
        print(f"Cleaned up temp file: {path}")
    except OSError as e:
        print(f"Error cleaning up file {path}: {e}")
