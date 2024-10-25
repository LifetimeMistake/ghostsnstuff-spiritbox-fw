from display import getDisplay
from speaker import piSpeaker
from microphone import piMic
from scipy.io import wavfile
import time
import numpy as np
rate, static1 = wavfile.read('./ghostsnstuff_spiritbox_fw/hal/interference_level1_2.wav')
spk = piSpeaker()
mic = piMic()
display = getDisplay()
if __name__ == "__main__":
    display.begin()
    # display.glitch(True)
    # time.sleep(5)
    # display.glitch(False)
    # display.printText("HelloWorld")
    display.sweep(True)
    spk.begin()
    spk.setInterference(1)
    time.sleep(1000000)
    # time.sleep(5)
    # display.sweep(True)
    # time.sleep(5)
    # display.sweep(False)
    # while True:
        # spk.playBuffer(static1, rate)
        # time.sleep(1)
    
    # mic.registerIconCallback(display.micIcon)
    # buffer = np.array([], dtype=np.float32)
    # buffer = mic.awaitBuffer()
    # display.thinkingIcon(True)
    # spk.playBuffer(buffer, 16000)
    # time.sleep(5)
    # display.thinkingIcon(False)
    # buffer = np.array([], dtype=np.float32)
    # buffer = mic.awaitBuffer()
    # spk.playBuffer(buffer, 16000)
    # display.begin()
    # display.noResponseIcon(True)