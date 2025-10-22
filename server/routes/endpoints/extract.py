import io
import asyncio
from uuid import uuid4
from fastapi import APIRouter, Request, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from ...store.nlp.interfaces import BaseGenerator
from ...services import MarkdownService

router = APIRouter(
    prefix="/data",
    tags=["Data"],
    responses={404: {"description": "Not found"}},
)

tasks = {}


def process_pdf_in_background(
    task_id: str, pdf_bytes: bytes, filename: str, generator: BaseGenerator
):
    try:
        service = MarkdownService(generator)
        md_content = asyncio.run(service.process_pdf(pdf_bytes))

        tasks[task_id] = {
            "status": "completed",
            "result": md_content,
            "filename": filename.replace(".pdf", ".md"),
        }
        print(f"Task {task_id} completed successfully.")

    except Exception as e:
        print(f"Task {task_id} failed: {e}")
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)


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
async def get_task_result(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    status = task.get("status")
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
        md_content = task.get("result")
        filename = task.get("filename", "converted.md")

        buffer = io.BytesIO(md_content.encode("utf-8"))
        headers = {"Content-Disposition": f"attachment; filename={filename}"}

        return StreamingResponse(buffer, media_type="text/markdown", headers=headers)

    raise HTTPException(status_code=500, detail="Unknown task status")
