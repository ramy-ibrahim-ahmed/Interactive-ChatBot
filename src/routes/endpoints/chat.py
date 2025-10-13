import json
import os
import shutil
import asyncio
import tempfile
from typing import AsyncGenerator, Dict, Any
from fastapi import APIRouter, Request, File, UploadFile, HTTPException, Form
from fastapi.responses import StreamingResponse
from ...store.nlp import NLPInterface
from ...store.vectordb import VectorDBInterface
from ...graph import init_workflow


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
    generator: NLPInterface = request.app.state.generator
    embeddings: NLPInterface = request.app.state.embeddings
    reranker: NLPInterface = request.app.state.reranker
    vectordb: VectorDBInterface = request.app.state.vectordb
    cachedb = request.app.state.cachedb

    if not query and not audio:
        raise HTTPException(
            status_code=400, detail="Either 'query' or 'audio' must be provided."
        )

    workflow = init_workflow(generator, embeddings, reranker, vectordb, cachedb)

    async def event_generator() -> AsyncGenerator[str, None]:
        user_message = query
        audio_path = None

        try:
            if audio:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
                    shutil.copyfileobj(audio.file, tmp)
                    audio_path = tmp.name

                transcribed_text = await generator.speech_to_text(audio_path)
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


@router.post("/tts")
async def generate_tts(request: Request, text: str = Form()):
    generator: NLPInterface = request.app.state.generator
    try:
        audio_path = await generator.text_to_speech(text)
        return {"audio_path": audio_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")
