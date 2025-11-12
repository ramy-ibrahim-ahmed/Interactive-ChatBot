import os
import asyncio
import tempfile
import structlog
from uuid import uuid4
from fastapi import APIRouter, Request, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from ...store.nlp.interfaces import BaseGenerator
from ...services import MarkdownService

LOGGER = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/data",
    tags=["Data"],
    responses={404: {"description": "Not found"}},
)

tasks = {}


def process_pdf_in_background(
    task_id: str, pdf_bytes: bytes, filename: str, generator: BaseGenerator
):
    temp_dir = None
    output_path = None
    try:
        temp_dir = tempfile.mkdtemp(prefix="onyx_task_")
        output_path = os.path.join(temp_dir, f"{task_id}.md")
        download_filename = filename.replace(".pdf", ".md")

        service = MarkdownService(generator)
        asyncio.run(service.process_pdf(pdf_bytes, output_path))

        tasks[task_id] = {
            "status": "completed",
            "temp_path": output_path,
            "filename": download_filename,
        }
        LOGGER.info(f"Task {task_id} completed successfully. Output: {output_path}")

    except Exception as e:
        LOGGER.exception(f"Task {task_id} failed: {e}")
        if task_id in tasks:
            tasks[task_id] = {"status": "failed", "error": str(e)}
        # Clean up temp dir on failure
        if temp_dir and os.path.exists(temp_dir):
            import shutil

            shutil.rmtree(temp_dir)


@router.post("/extract")
async def start_pdf_to_markdown_conversion(
    request: Request,
    background_tasks: BackgroundTasks,
    pdf_file: UploadFile = File(...),
):
    if not pdf_file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    pdf_bytes = await pdf_file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Empty PDF file")

    task_id = str(uuid4())
    tasks[task_id] = {"status": "processing"}

    generator: BaseGenerator = request.app.state.generators.get("gemini")

    background_tasks.add_task(
        process_pdf_in_background, task_id, pdf_bytes, pdf_file.filename, generator
    )

    return {
        "task_id": task_id,
        "status": "processing",
        "message": "PDF processing started.",
    }


@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    response_data = {"status": task.get("status")}
    if task.get("status") == "failed":
        response_data["error"] = task.get("error")

    return response_data


@router.get("/result/{task_id}")
async def get_task_result(task_id: str, background_tasks: BackgroundTasks):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    status = task.get("status")
    LOGGER.info(f"Result request for task {task_id}, status: {status}")

    if status == "processing":
        return JSONResponse(
            status_code=202,
            content={
                "status": "processing",
                "message": "The task is still running. Please try again later.",
            },
        )
    if status == "failed":
        raise HTTPException(
            status_code=500, detail=f"Processing failed: {task.get('error')}"
        )
    if status == "completed":
        temp_path = task.get("temp_path")
        download_filename = task.get("filename", "converted.md")

        if not temp_path or not os.path.exists(temp_path):
            LOGGER.error(f"Result file missing for task {task_id}: {temp_path}")
            raise HTTPException(status_code=500, detail="Result file not found")

        safe_filename = download_filename.replace('"', '\\"')
        headers = {"Content-Disposition": f'attachment; filename="{safe_filename}"'}
        background_tasks.add_task(lambda tid=task_id: _cleanup_task_entry(tid))
        return FileResponse(temp_path, media_type="text/markdown", headers=headers)

    LOGGER.error(f"Unknown task status for {task_id}: {status}")
    raise HTTPException(status_code=500, detail="Unknown task status")


def _cleanup_task_entry(task_id: str):
    """Helper: Remove task entry 30s after download starts (safe, idempotent)."""
    import time

    time.sleep(30)
    if task_id in tasks:
        del tasks[task_id]
        LOGGER.info(f"Cleaned task entry: {task_id}")
