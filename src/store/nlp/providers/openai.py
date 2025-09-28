import os
import re
import numpy as np
from uuid import uuid4
from ..interface import NLPInterface


class OpenAIProvider(NLPInterface):
    def __init__(self, openai_client):
        self.openai_client = openai_client

    def embed(self, list_of_text, batch_size=1, model_name="text-embedding-3-large"):
        vectors = []
        for i in range(0, len(list_of_text), batch_size):
            batch = list_of_text[i : i + batch_size]
            response = self.openai_client.embeddings.create(
                input=batch, model=model_name
            )
            batch_vectors = [item.embedding for item in response.data]
            batch_vectors = [
                (vec / np.linalg.norm(vec)) if np.linalg.norm(vec) != 0 else vec
                for vec in batch_vectors
            ]
            vectors.extend(batch_vectors)
        return vectors

    def chat(self, messages: list[dict], model_name: str) -> list[list[float]]:
        # response = self.openai_client.beta.chat.completions.parse(
        #     model=model_name, messages=messages, temperature=0.0, top_p=1.0
        # )
        response = self.openai_client.beta.chat.completions.parse(
            model=model_name, messages=messages
        )
        return response.choices[0].message.content

    def structured_chat(self, response_model, model_name, messages):
        response = self.openai_client.beta.chat.completions.parse(
            model=model_name,
            messages=messages,
            response_format=response_model,
            temperature=0.0,
            top_p=1.0,
        )
        msg = response.choices[0].message
        return msg.parsed

    def text_to_speech(self, text):
        cleaned_text = re.sub(r"[#*\-]\s?", "", text)
        speech_dir = "src/assets/audio/"
        speech_filename = str(uuid4()) + ".wav"
        speech_file_path = os.path.join(speech_dir, speech_filename)
        os.makedirs(speech_dir, exist_ok=True)

        instructions = """Tone: The voice should be refined, formal, and delightfully theatrical, reminiscent of a charming radio announcer from the early 20th century.\n\nPacing: The speech should flow smoothly at a steady cadence, neither rushed nor sluggish, allowing for clarity and a touch of grandeur.\n\nPronunciation: Words should be enunciated crisply and elegantly, with an emphasis on vintage expressions and a slight flourish on key phrases.\n\nEmotion: The delivery should feel warm, enthusiastic, and welcoming, as if addressing a distinguished audience with utmost politeness.\n\nInflection: Gentle rises and falls in pitch should be used to maintain engagement, adding a playful yet dignified flair to each sentence.\n\nWord Choice: The script should incorporate vintage expressions like splendid, marvelous, posthaste, and ta-ta for now, avoiding modern slang."""
        with self.openai_client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=cleaned_text,
            instructions=instructions,
        ) as response:
            response.stream_to_file(speech_file_path)
        url_path = "/" + speech_file_path.replace("\\", "/").split("src/", 1)[1]
        return url_path

    def speech_to_text(self, audio_path):
        audio_file = open(audio_path, "rb")
        transcription = self.openai_client.audio.transcriptions.create(
            model="gpt-4o-transcribe", file=audio_file
        )
        return transcription.text

    def rerank(self, query, documents, model_name): ...
