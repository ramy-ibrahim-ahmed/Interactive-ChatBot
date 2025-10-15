import os
import json
import shutil
import asyncio
import time
import tempfile
from typing import AsyncGenerator, Dict, Any
from fastapi import (
    APIRouter,
    Request,
    File,
    UploadFile,
    HTTPException,
    Form,
    BackgroundTasks,
)
from fastapi.responses import StreamingResponse
from ...robot import init_workflow


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
    responses={404: {"description": "Not found"}},
)


def _format_sse_message(event_data: Dict[str, Any]) -> str:
    return f"data: {json.dumps(event_data)}\n\n"


def _serialize_if_needed(data: Any) -> Any:
    return data.dict() if hasattr(data, "dict") else data


async def _stream_workflow_events(
    workflow, user_message: str
) -> AsyncGenerator[str, None]:

    try:
        async for event in workflow.astream_events(
            {"user_message": user_message, "session_id": "123"}, version="v2"
        ):
            kind = event["event"]
            name = event["name"]

            if kind == "on_chain_start" and name != "LangGraph":
                event_data = {"event": "start_node", "node": name}
                yield _format_sse_message(event_data)
                await asyncio.sleep(0.1)

            elif kind == "on_chain_stream" and name == "chat":
                if chunk := event["data"].get("chunk"):
                    event_data = {"event": "stream_chunk", "data": chunk}
                    yield _format_sse_message(event_data)
                    await asyncio.sleep(0.01)

            elif kind == "on_chain_end" and name == "LangGraph":
                final_state = event["data"]["output"]
                final_payload = {
                    "answer": final_state.get("response"),
                    "enhanced_query": _serialize_if_needed(
                        final_state.get("enhanced_query")
                    ),
                    "search_results": _serialize_if_needed(
                        final_state.get("search_results")
                    ),
                    "user_message": final_state.get("user_message"),
                }
                event_data = {"event": "final_answer", "data": final_payload}
                yield _format_sse_message(event_data)

    except Exception as e:
        print(f"Error during streaming: {e}")
        error_data = {"event": "error", "message": str(e)}
        yield _format_sse_message(error_data)


@router.post("")
async def chat(
    request: Request, query: str = Form(None), audio: UploadFile = File(None)
):
    generator = request.app.state.generator
    embeddings = request.app.state.embeddings
    reranker = request.app.state.reranker
    vectordb = request.app.state.vectordb
    lexical_search = request.app.state.lexical_search
    cachedb = request.app.state.cachedb
    stt = request.app.state.stt

    if not query and not audio:
        raise HTTPException(
            status_code=400, detail="Either 'query' or 'audio' must be provided."
        )

    workflow = init_workflow(
        generator, embeddings, reranker, vectordb, lexical_search, cachedb
    )

    async def event_generator() -> AsyncGenerator[str, None]:
        user_message = query
        audio_path = None

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
                await asyncio.sleep(0.01)

            async for event in _stream_workflow_events(workflow, user_message):
                yield event

        finally:
            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def cleanup_file(path: str):
    try:
        time.sleep(60)
        os.remove(path)
        print(f"Cleaned up temp file: {path}")
    except OSError as e:
        print(f"Error cleaning up file {path}: {e}")


@router.post("/tts")
async def generate_tts(
    request: Request, background_tasks: BackgroundTasks, text: str = Form()
):
    tts = request.app.state.tts
    try:
        url_path, full_file_path = await tts.text_to_speech(text)

        background_tasks.add_task(cleanup_file, full_file_path)

        return {"audio_path": url_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")
