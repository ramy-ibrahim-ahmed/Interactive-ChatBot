import os
import json
import logging
import tempfile
from fastapi import APIRouter, Request, UploadFile, File, HTTPException, Query
from fastapi.responses import Response
from ...store.nlp.interfaces import BaseGenerator, BaseEmbeddings
from ...store.semantic import VectorDBInterface
from ...services import ChunkService


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/data",
    tags=["Data"],
    responses={404: {"description": "Not found"}},
)


@router.post("/chunk")
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

    generator: BaseGenerator = request.app.state.generators.get("gemini")
    embeddings: BaseEmbeddings = request.app.state.embeddings
    vectordb: VectorDBInterface = request.app.state.vectordb
    service = ChunkService(generator, embeddings, vectordb)

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
        json_data = [item.model_dump() for item in data]

        json_str = json.dumps(json_data, indent=4, ensure_ascii=False)

        headers = {
            "Content-Disposition": f"attachment; filename={collection_name}.json"
        }

        return Response(
            content=json_str, media_type="application/json", headers=headers
        )
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
