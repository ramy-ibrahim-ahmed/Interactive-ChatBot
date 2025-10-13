import io
from fastapi import APIRouter, Request, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from ...store.nlp.interfaces import BaseGenerator
from ...services import MarkdownService


router = APIRouter(
    prefix="/data",
    tags=["Data"],
    responses={404: {"description": "Not found"}},
)


@router.post("/extract")
async def convert_pdf_to_markdown(request: Request, pdf_file: UploadFile = File(...)):
    if not pdf_file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    generator: BaseGenerator = request.app.state.generator
    settings = request.app.state.settings
    service = MarkdownService(generator, settings)

    try:

        pdf_bytes = await pdf_file.read()
        if not pdf_bytes:
            raise HTTPException(status_code=400, detail="Empty PDF file")

        md_content = await service.process_pdf(pdf_bytes)
        if not md_content:
            raise HTTPException(
                status_code=500, detail="Failed to generate Markdown content"
            )

        buffer = io.BytesIO(md_content.encode("utf-8"))
        filename = pdf_file.filename.replace(".pdf", ".md")
        headers = {"Content-Disposition": f"attachment; filename={filename}"}
        return StreamingResponse(buffer, media_type="text/markdown", headers=headers)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
