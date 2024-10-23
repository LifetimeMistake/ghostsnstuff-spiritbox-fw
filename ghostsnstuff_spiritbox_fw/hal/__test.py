from display import getDisplay
from speaker import piSpeaker
from microphone import piMic
from scipy.io import wavfile
import time
import numpy as np

spk = piSpeaker()
mic = piMic()
display = getDisplay()
if __name__ == "__main__":

    buffer = np.array([], dtype=np.float32)
    buffer = mic.awaitBuffer()
    spk.playBuffer(buffer, 16000)