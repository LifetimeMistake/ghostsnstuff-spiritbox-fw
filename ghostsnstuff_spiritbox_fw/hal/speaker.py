from abc import ABC
import numpy as np
import pyaudio
import __audio_define as audef
import threading
from scipy.io import wavfile

pa = pyaudio.PyAudio()

__stop_interference = 1

static1 = None
def __load_static_files():
    global static1
    rate, static1 = wavfile.read("./ghostsnstuff_spiritbox_fw/hal/audio/interference_level1_2.wav")

def __play_numpy_buffer_thread(buffer, sample_rate, channels, chunk_size):
    if buffer.ndim > 1:
        buffer = buffer.mean(axis=1)
    stream = pa.open(format=audef.speaker_pa_format, channels=channels, rate=sample_rate, output=True, frames_per_buffer=audef.speaker_chunk_size)
    buffer = buffer.astype(audef.speaker_np_format)
    max_val = np.max(np.abs(buffer))
    if max_val >0:
        buffer /= max_val

    index = 0
    buffer_size = len(buffer)
    while index < buffer_size:
        chunk = buffer[index:index + 1024]
        if len(chunk) < 1024:
            chunk = np.pad(chunk, (0,1024 - len(chunk)), 'constant')
        stream.write(chunk.tobytes())
        index += 1024

    stream.stop_stream()
    stream.close()

def __simulate_interferance_thread():
    __play_numpy_buffer_thread()    

def __setInterference(value):
    if (value == 0):
        global __stop_interference
        __stop_interference = 1

def play_numpy_buffer(buffer, sample_rate, channels, chunk_size):
    playbackThread = threading.Thread(target=__play_numpy_buffer_thread, args=(buffer, sample_rate, channels, chunk_size))
    playbackThread.start()


class speaker(ABC):
    def playBuffer(self, buffer, sample_rate):
        pass
    def begin(self):
        pass
    def setInterference(self):
        pass

class piSpeaker(speaker):
    def playBuffer(self, buffer, sample_rate):
        play_numpy_buffer(buffer, sample_rate, audef.speaker_channels, audef.speaker_chunk_size)
    def begin(self):
        __load_static_files()
    def setInterference(self, value):
        __setInterference(value)
        


# def getSpeaker():
#     return piSpeaker()