import pyaudio
import numpy as np
import webrtcvad
import collections
import threading
import time
import __audio_define as audef
from abc import ABC
# Constants


# Initialize PyAudio, WebRTC VAD
pa = pyaudio.PyAudio()
vad = webrtcvad.Vad(audef.mic_vad_mode)

# Circular buffer for 1 second audio
circular_buffer = collections.deque(maxlen=audef.mic_circular_buffer_size)
_iconCallback = None

# Lock for synchronization
_buffer_lock = threading.Lock()
_recording_event = threading.Event()
_result_buffer = np.array([], dtype=np.int16)  # Ensure correct initialization

def _mic_callback(in_data, frame_count, time_info, status_flags):
    global _result_buffer
    audio_frame = np.frombuffer(in_data, dtype=np.int16)

    with _buffer_lock:
        circular_buffer.extend(audio_frame)

    if _recording_event.is_set():
        _result_buffer = np.append(_result_buffer, audio_frame)

    return (None, pyaudio.paContinue)

def _vad():
    global _result_buffer
    num_voiced_frames = 0
    num_unvoiced_frames = 0
    required_voiced_frames = 10
    required_unvoiced_frames = 20

    while True:
        time.sleep(audef.mic_frame_duration_ms / 1000.0)

        with _buffer_lock:
            if len(circular_buffer) < audef.mic_frame_size:
                continue

            frame = np.array(circular_buffer)[-audef.mic_frame_size:]
            is_speech = vad.is_speech(frame.tobytes(), audef.mic_sample_rate)

        if is_speech:
            print("is speech")
            if (_iconCallback is not None):
                _iconCallback(True)
            num_voiced_frames += 1
            num_unvoiced_frames = 0

            if num_voiced_frames >= required_voiced_frames and not _recording_event.is_set():
                with _buffer_lock:
                    _recording_event.set()
                    #_result_buffer = np.array(circular_buffer, dtype=np.int16)
                    _result_buffer = np.append(np.array(circular_buffer, dtype=np.int16), _result_buffer)
        else:
            print("is not speech")
            if (_iconCallback is not None):
                _iconCallback(False)
            if _recording_event.is_set():
                num_unvoiced_frames += 1
                if num_unvoiced_frames >= required_unvoiced_frames:
                    _recording_event.clear()
                    break
            else:
                num_unvoiced_frames += 1

def _awaitBuffer():
    global _result_buffer
    _result_buffer = np.array([], dtype=np.int16)  # Reset buffer for new recording
    stream = pa.open(
        format=audef.mic_pa_format,
        channels=audef.mic_channels,
        rate=audef.mic_sample_rate,
        input=True,
        frames_per_buffer=audef.mic_frame_size,
        stream_callback=_mic_callback
    )

    stream.start_stream()
    _vad()

    while _recording_event.is_set():
        time.sleep(0.1)

    stream.stop_stream()
    stream.close()

    return _result_buffer.astype(np.float32) / 32768.0


class microphone(ABC):
    def awaitBuffer(self):
        pass
    def registerIconCallback(self, callback):
        pass
    def unregisterIconCallback(self):
        pass

class piMic(microphone):
    def awaitBuffer(self):
        return _awaitBuffer()
    def registerIconCallback(self, callback):
        global _iconCallback
        _iconCallback = callback
    def unregisterIconCallback(self):
        global _iconCallback
        _iconCallback = None