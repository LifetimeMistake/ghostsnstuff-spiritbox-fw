from openai import OpenAI
from typing import Self, Literal
import numpy as np
from scipy.io.wavfile import write
import io
import soundfile as sf

VOICE_MODELS = Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

class TTSClient:
    def __init__(self, client: OpenAI) -> Self:
        self.client = client

    def synthesize(self, content: str, voice_model: str, speed: float = 1.0) -> np.ndarray:
        print(content)
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

def numpy_to_wav(buffer, sample_rate):
    pcm_int16 = np.int16(buffer * 32767)
    memory_buffer = io.BytesIO()
    sf.write(memory_buffer, buffer, sample_rate, format='WAV', subtype='FLOAT')
    memory_buffer.seek(0)
    with open("output.wav", "wb") as f:
        f.write(memory_buffer.read())
    return memory_buffer

class STTClient:
    def __init__(self, client: OpenAI) -> Self:
        self.client = client

    def transcribe(self, buffer, sample_rate):
        wav_io = numpy_to_wav(buffer, sample_rate)
        audio_file = open("output.wav", "rb")
        return self.client.audio.transcriptions.create(model="whisper-1", file=audio_file, response_format="text")