import os
import json
from typing import List
from fastapi import APIRouter, Request, UploadFile, File, HTTPException, Query
from ...store.nlp.interfaces import BaseEmbeddings
from ...store.semantic import VectorDBInterface
from ...store.lexical.index import LexicalTrainer

router = APIRouter(
    prefix="/data",
    tags=["Data"],
    responses={404: {"description": "Not found"}},
)


async def _process_json_file_and_get_chunks(json_file: UploadFile) -> List[str]:
    if not json_file.filename.lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="File must be a JSON file")

    content = await json_file.read()
    try:
        data = json.loads(content)
        return [chunk for item in data for chunk in item["chunks"]]
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format.")
    except (KeyError, TypeError):
        raise HTTPException(
            status_code=400,
            detail="JSON structure is invalid. Expected a list of objects, each with a 'chunks' key.",
        )


@router.post("/index/semantic")
async def index_semantic(
    request: Request,
    json_file: UploadFile = File(...),
    collection_name: str = Query(...),
):
    flatten_chunks = await _process_json_file_and_get_chunks(json_file)
    embeddings_service: BaseEmbeddings = request.app.state.embeddings
    vectordb: VectorDBInterface = request.app.state.vectordb
    embedded_vectors = await embeddings_service.embed(flatten_chunks, batch_size=10)
    metadata = [{"text": text} for text in flatten_chunks]
    vectordb.upsert(embedded_vectors, metadata, collection_name, batch_size=100)
    return {"message": "Data indexed successfully"}


@router.post("/index/lexical")
async def index_lexical(
    request: Request,
    json_file: UploadFile = File(...),
    collection_name: str = Query(...),
):
    os.makedirs("models", exist_ok=True)
    model_save_path = f"models/{collection_name}.json"
    flatten_chunks = await _process_json_file_and_get_chunks(json_file)
    lexical_trainer: LexicalTrainer = request.app.state.lexical_trainer
    lexical_trainer.train_and_index(
        corpus=flatten_chunks,
        namespace=collection_name,
        model_save_path=model_save_path,
    )
    return {"message": "Data indexed successfully"}
