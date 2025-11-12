import os
import json
import shutil
import tempfile
from datetime import datetime
from typing import AsyncGenerator, Literal
from fastapi import APIRouter, Request, HTTPException, Form, BackgroundTasks
from fastapi import File, UploadFile
from fastapi.responses import StreamingResponse
from ...robot import init_workflow
from ...services import ChatHistoryServie
from ..background import update_chat_history_task
from ..utils import stream_workflow_events, _format_sse_message

LOG_FILE = "/logs/chat_turns_log.json"

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
    responses={404: {"description": "Not found"}},
)


@router.post("")
async def chat(
    request: Request,
    background_tasks: BackgroundTasks,
    session_id: str = Form("default-session"),
    query: str = Form(None),
    audio: UploadFile = File(None),
    provider: Literal["gemini", "openai", "ollama"] = Form("gemini"),
):

    generator = request.app.state.generators.get(provider)
    embeddings = request.app.state.embeddings
    reranker = request.app.state.reranker
    vectordb = request.app.state.vectordb
    cachedb = request.app.state.cachedb
    stt = request.app.state.stt

    if not query and not audio:
        raise HTTPException(
            status_code=400, detail="Either 'query' or 'audio' must be provided."
        )

    history_service = ChatHistoryServie(cachedb=cachedb, generator=generator)
    previous_summary = await history_service.get_summary(session_id)

    workflow = init_workflow(generator, embeddings, reranker, vectordb)

    async def event_generator() -> AsyncGenerator[str, None]:
        user_message = query
        audio_path = None
        final_ai_response = None
        final_search_results = None

        try:
            if audio:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
                    shutil.copyfileobj(audio.file, tmp)
                    audio_path = tmp.name

                transcribed_text = await stt.speech_to_text(audio_path)
                user_message = transcribed_text

                transcribed_event = {
                    "event": "transcribed",
                    "data": {"user_message": user_message},
                }
                yield _format_sse_message(transcribed_event)

            streamer = stream_workflow_events(
                workflow, user_message, previous_summary or ""
            )

            async for event_str in streamer:
                if event_str.startswith("data:"):
                    try:
                        event_json = json.loads(event_str[len("data: ") :])
                        if event_json.get("event") == "final_answer":
                            final_data = event_json.get("data", {})
                            final_ai_response = final_data.get("answer")
                            final_search_results = final_data.get("search_results")
                    except json.JSONDecodeError:
                        pass
                yield event_str

            if user_message and final_ai_response:
                search_str = (
                    json.dumps(final_search_results, ensure_ascii=False)
                    if final_search_results
                    else ""
                )

                log_entry = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "session_id": session_id,
                    "user_message": user_message,
                    "search_str": search_str,
                    "final_ai_response": final_ai_response,
                }
                os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
                with open(LOG_FILE, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

                background_tasks.add_task(
                    update_chat_history_task,
                    session_id=session_id,
                    user_message=user_message,
                    search=search_str,
                    ai_response=final_ai_response,
                    cachedb=cachedb,
                    generator=generator,
                )

        finally:
            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
