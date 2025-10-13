import os
import re
from uuid import uuid4
from openai import AsyncOpenAI
from ..interfaces import BaseTTS


class OpenAITTS(BaseTTS):
    def __init__(self, openai_client):
        self.openai_client: AsyncOpenAI = openai_client

    async def text_to_speech(self, text):
        cleaned_text = re.sub(r"[#*\-]\s?", "", text)
        speech_dir = "src/assets/audio/"
        speech_filename = str(uuid4()) + ".wav"
        speech_file_path = os.path.join(speech_dir, speech_filename)
        os.makedirs(speech_dir, exist_ok=True)

        instructions = """Tone: The voice should be refined, formal, and delightfully theatrical, reminiscent of a charming radio announcer from the early 20th century.\n\nPacing: The speech should flow smoothly at a steady cadence, neither rushed nor sluggish, allowing for clarity and a touch of grandeur.\n\nPronunciation: Words should be enunciated crisply and elegantly, with an emphasis on vintage expressions and a slight flourish on key phrases.\n\nEmotion: The delivery should feel warm, enthusiastic, and welcoming, as if addressing a distinguished audience with utmost politeness.\n\nInflection: Gentle rises and falls in pitch should be used to maintain engagement, adding a playful yet dignified flair to each sentence.\n\nWord Choice: The script should incorporate vintage expressions like splendid, marvelous, posthaste, and ta-ta for now, avoiding modern slang."""
        async with self.openai_client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=cleaned_text,
            instructions=instructions,
        ) as response:
            await response.stream_to_file(speech_file_path)
        url_path = "/" + speech_file_path.replace("\\", "/").split("src/", 1)[1]
        return url_path
