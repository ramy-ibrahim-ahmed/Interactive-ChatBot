from fastapi import APIRouter, Request, HTTPException, Form, BackgroundTasks
from ..background import cleanup_file_task

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
    responses={404: {"description": "Not found"}},
)


@router.post("/tts")
async def generate_tts(
    request: Request, background_tasks: BackgroundTasks, text: str = Form()
):
    tts = request.app.state.tts
    try:
        url_path, full_file_path = await tts.text_to_speech(text)
        # background_tasks.add_task(cleanup_file_task, full_file_path)
        return {"audio_path": url_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")
