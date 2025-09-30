from pydantic import BaseModel
from fastapi import APIRouter, Request, File, UploadFile, HTTPException, Form
from ....store.nlp import NLPInterface
from ....store.vectordb import VectorDBInterface
from ....graph import init_workflow
import os
import tempfile
import shutil
from pathlib import Path
import time

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
    responses={404: {"description": "Not found"}},
)


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
    start = time.time()
    response = workflow.invoke({"user_message": user_message})
    end = time.time()

    if response.get("intent") != "ERP":
        return {"answer": "I cant help."}

    return {
        "time": end - start,
        "answer": response.get("response"),
        "analysis": response.get("analysis"),
        "enhanced_query": response.get("enhanced_query"),
        "search_results": response.get("search_results"),
        "audio_path": response.get("audio_path"),
    }
