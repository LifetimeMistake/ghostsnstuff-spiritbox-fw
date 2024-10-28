import pyaudio
import numpy as np
import webrtcvad
import collections
import threading
import time
from abc import ABC, abstractmethod

# Constants for audio settings
MIC_SAMPLE_RATE = 16000
MIC_CHANNELS = 1
MIC_PREBUFFER_SECONDS = 1
MIC_PA_FORMAT = pyaudio.paInt16
MIC_NP_FORMAT = np.int16
MIC_FRAME_DURATION_MS = 30
MIC_FRAME_SIZE = int(MIC_SAMPLE_RATE * (MIC_FRAME_DURATION_MS / 1000))
MIC_CIRCULAR_BUFFER_SIZE = MIC_SAMPLE_RATE * MIC_PREBUFFER_SECONDS
MIC_VAD_MODE = 3
REQUIRED_VOICED_FRAMES = 30
REQUIRED_UNVOICED_FRAMES = 50


class Microphone(ABC):
    @abstractmethod
    def await_buffer(self):
        """Waits for a voice-activated audio buffer and returns the captured audio."""
        pass

    @abstractmethod
    def register_icon_callback(self, callback):
        """Registers a callback function to handle VAD state changes."""
        pass

    @abstractmethod
    def unregister_icon_callback(self):
        """Unregisters the VAD state change callback function."""
        pass

    @abstractmethod
    def get_sample_rate(self) -> int:
        """returns the sample rate in Hz"""
        pass


class PaMicrophone(Microphone):
    def __init__(self):
        self.pa = pyaudio.PyAudio()
        self.vad = webrtcvad.Vad(MIC_VAD_MODE)
        self.circular_buffer = collections.deque(maxlen=MIC_CIRCULAR_BUFFER_SIZE)
        self._icon_callback = None
        self._buffer_lock = threading.Lock()
        self._recording_event = threading.Event()
        self._result_buffer = np.array([], dtype=MIC_NP_FORMAT)

    def _mic_callback(self, in_data, frame_count, time_info, status_flags):
        audio_frame = np.frombuffer(in_data, dtype=MIC_NP_FORMAT)
        
        with self._buffer_lock:
            self.circular_buffer.extend(audio_frame)
        
        if self._recording_event.is_set():
            self._result_buffer = np.append(self._result_buffer, audio_frame)

        return (None, pyaudio.paContinue)

    def _detect_vad(self):
        num_voiced_frames = 0
        num_unvoiced_frames = 0

        while True:
            time.sleep(MIC_FRAME_DURATION_MS / 1000.0)
            
            with self._buffer_lock:
                if len(self.circular_buffer) < MIC_FRAME_SIZE:
                    continue
                
                frame = np.array(self.circular_buffer)[-MIC_FRAME_SIZE:]
                is_speech = self.vad.is_speech(frame.tobytes(), MIC_SAMPLE_RATE)
            
            if is_speech:
                if self._icon_callback:
                    self._icon_callback(True)
                num_voiced_frames += 1
                num_unvoiced_frames = 0

                if num_voiced_frames >= REQUIRED_VOICED_FRAMES and not self._recording_event.is_set():
                    with self._buffer_lock:
                        self._recording_event.set()
                        self._result_buffer = np.append(np.array(self.circular_buffer, dtype=MIC_NP_FORMAT), self._result_buffer)
            else:
                if self._icon_callback:
                    self._icon_callback(False)
                if self._recording_event.is_set():
                    num_unvoiced_frames += 1
                    if num_unvoiced_frames >= REQUIRED_UNVOICED_FRAMES:
                        self._recording_event.clear()
                        break
                else:
                    num_unvoiced_frames += 1

    def await_buffer(self):
        self._result_buffer = np.array([], dtype=MIC_NP_FORMAT)
        stream = self.pa.open(
            format=MIC_PA_FORMAT,
            channels=MIC_CHANNELS,
            rate=MIC_SAMPLE_RATE,
            input=True,
            frames_per_buffer=MIC_FRAME_SIZE,
            stream_callback=self._mic_callback
        )

        stream.start_stream()
        self._detect_vad()

        while self._recording_event.is_set():
            time.sleep(0.1)

        stream.stop_stream()
        stream.close()

        return self._result_buffer.astype(np.float32) / 32768.0

    def register_icon_callback(self, callback):
        self._icon_callback = callback

    def unregister_icon_callback(self):
        self._icon_callback = None

    def get_sample_rate(self) -> int:
        return MIC_SAMPLE_RATE


def get_microphone() -> Microphone:
    return PaMicrophone()
