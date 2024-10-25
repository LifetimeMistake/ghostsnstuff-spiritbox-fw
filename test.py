from ghostsnstuff_spiritbox_fw.hal.display import getDisplay
from ghostsnstuff_spiritbox_fw.hal.speaker import getSpeaker
from ghostsnstuff_spiritbox_fw.hal.microphone import getMic
import time

disp = getDisplay()
spk = getSpeaker()
mic = getMic()

disp.begin()
spk.begin()
mic.registerIconCallback(disp.micIcon)
# print("0")
# spk.setInterference(1)
# time.sleep(10)
print("1")
time.sleep(1)
disp.glitch(True)
spk.setInterference(2)
time.sleep(0.5)
disp.glitch(False)