from openai import AsyncOpenAI
from ..interfaces import BaseSTT


class OpenAISTT(BaseSTT):
    def __init__(self, openai_client):
        self.openai_client: AsyncOpenAI = openai_client

    async def speech_to_text(self, audio_path):
        audio_file = open(audio_path, "rb")
        transcription = await self.openai_client.audio.transcriptions.create(
            model="gpt-4o-transcribe", file=audio_file
        )
        return transcription.text
