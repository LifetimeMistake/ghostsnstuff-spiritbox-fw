from openai import OpenAI
from typing import Self, Literal
import numpy as np

VOICE_MODELS = Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

class TTSClient:
    def __init__(self, client: OpenAI) -> Self:
        self.client = client

    def synthesize(self, content: str, voice_model: str, speed: float = 1.0) -> np.ndarray:
        response = self.client.audio.speech.create(
            model="tts-1",
            voice=voice_model,
            input=content,
            response_format="pcm",
            speed=speed,
            timeout=2
        )

        pcm_data = np.frombuffer(response.content, dtype=np.int16)  # assuming 16-bit PCM data
        audio_data = pcm_data.astype(np.float32) / 32768.0  # normalize to range -1.0 to 1.0
        return audio_data

    def synthesize_batch(self, content: list[str], voice_model: str, speed: float = 1.0) -> list[np.ndarray]:
        return [self.synthesize(text, voice_model, speed) for text in content]