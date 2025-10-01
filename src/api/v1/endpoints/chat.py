import json
import shutil
import asyncio
import tempfile
from fastapi import APIRouter, Request, File, UploadFile, HTTPException, Form
from fastapi.responses import StreamingResponse, JSONResponse
from ....store.nlp import NLPInterface
from ....store.vectordb import VectorDBInterface
from ....graph import init_workflow

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
    responses={404: {"description": "Not found"}},
)


async def stream_events(workflow, user_message: str):
    try:
        async for event in workflow.astream_events(
            {"user_message": user_message}, version="v2"
        ):
            kind = event["event"]
            name = event["name"]

            if kind == "on_chain_start" and name != "LangGraph":
                event_data = {"event": "start_node", "node": name}
                yield f"data: {json.dumps(event_data)}\n\n"
                await asyncio.sleep(0.1)

            elif kind == "on_chain_end" and name == "LangGraph":
                final_state = event["data"]["output"]

                enhanced_query = final_state.get("enhanced_query")
                search_results = final_state.get("search_results")

                final_payload = {
                    "answer": final_state.get("response"),
                    "analysis": final_state.get("analysis"),
                    "enhanced_query": (
                        enhanced_query.dict()
                        if hasattr(enhanced_query, "dict")
                        else enhanced_query
                    ),
                    "search_results": (
                        search_results.dict()
                        if hasattr(search_results, "dict")
                        else search_results
                    ),
                    "user_message": final_state.get("user_message"),
                }  # Removed audio_path here to avoid auto-generation

                event_data = {"event": "final_answer", "data": final_payload}
                yield f"data: {json.dumps(event_data)}\n\n"

    except Exception as e:
        print(f"Error during streaming: {e}")
        error_data = {"event": "error", "message": str(e)}
        yield f"data: {json.dumps(error_data)}\n\n"


@router.post("")
async def chat(
    request: Request, query: str = Form(None), audio: UploadFile = File(None)
):
    vectordb: VectorDBInterface = request.app.state.vectordb
    nlp_openai: NLPInterface = request.app.state.nlp_openai
    nlp_gemini: NLPInterface = request.app.state.nlp_gemini
    nlp_cohere: NLPInterface = request.app.state.nlp_cohere

    if audio:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            shutil.copyfileobj(audio.file, tmp)
            audio_path = tmp.name
        transcribed = nlp_openai.speech_to_text(audio_path)
        user_message = transcribed
    elif query:
        user_message = query
    else:
        raise HTTPException(status_code=400, detail="Provide either query or audio")

    workflow = init_workflow(nlp_openai, nlp_gemini, nlp_cohere, vectordb)

    return StreamingResponse(
        stream_events(workflow, user_message), media_type="text/event-stream"
    )


@router.post("/tts")
async def generate_tts(request: Request, text: str = Form()):
    nlp_openai: NLPInterface = request.app.state.nlp_openai
    try:
        audio_path = nlp_openai.text_to_speech(text)
        return JSONResponse({"audio_path": audio_path})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")
