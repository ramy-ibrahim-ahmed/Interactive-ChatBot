import os
import json
import logging
import tempfile
from fastapi import APIRouter, Request, UploadFile, File, HTTPException, Query
from ...store.nlp import NLPInterface
from ...store.vectordb import VectorDBInterface
from ...services import ProcessService


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/data",
    tags=["Data"],
    responses={404: {"description": "Not found"}},
)


@router.post("/process")
async def process_markdown(
    request: Request,
    md_file: UploadFile = File(...),
    separator: str = Query(default="---#---"),
    boundaries: str = Query(...),
    num_toc_pages: int = Query(...),
    collection_name: str = Query(...),
):
    if not md_file.filename.lower().endswith(".md"):
        raise HTTPException(status_code=400, detail="File must be a Markdown file")

    nlp_openai: NLPInterface = request.app.state.nlp_openai
    nlp_cohere: NLPInterface = request.app.state.nlp_cohere
    vectordb: VectorDBInterface = request.app.state.vectordb
    service = ProcessService(nlp_openai, nlp_cohere, vectordb)

    try:
        try:
            boundaries_list = [
                int(x.strip()) for x in boundaries.split(",") if x.strip()
            ]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Boundaries must be a comma-separated list of integers",
            )

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp:
            content = await md_file.read()
            tmp.write(content)
            file_path = tmp.name

        data = await service.chunk(file_path, separator, boundaries_list, num_toc_pages)
        os.makedirs("output", exist_ok=True)
        json_data = [item.model_dump() for item in data]

        with open(f"output/{collection_name}.json", "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False)

        flatten = list()
        for many_chunk in data:
            flatten.extend(many_chunk.chunks)

        service.upsert(flatten, collection_name)
        return {"message": "Data processed and uploaded successfully"}
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
