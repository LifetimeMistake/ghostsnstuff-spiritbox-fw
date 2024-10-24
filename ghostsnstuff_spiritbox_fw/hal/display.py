from abc import ABC, abstractclassmethod
import platform
import threading
import time
import random

_win_display = False

system = platform.system()
def isOnPi():

    if "Linux" in system and "arm" in platform.machine():
        return True
    else:
        return False
    
def isOnWin():
    if "Windows" in system:
        return True
    else:
        return False
if isOnWin():

    from PIL import Image, ImageDraw, ImageFont, ImageTk
    import tkinter as tk

if (isOnPi()):
    import st7735
    import PIL
    global disp
    disp = st7735.ST7735(port=0,cs=st7735.BG_SPI_CS_BACK,dc="GPIO9",backlight="GPIO12", rotation=90, spi_speed_hz=4000000)
    
    def _pushBuffer(buffer):
        disp.display(buffer)

img = Image.new('RGB', (160, 80), color=(248, 133, 18))
font = ImageFont.truetype("./ghostsnstuff_spiritbox_fw/hal/DSEG14Modern-Italic.ttf", 30)
micIcon = Image.open("./ghostsnstuff_spiritbox_fw/hal/icons/mic.png")
micDisabledIcon = Image.open("./ghostsnstuff_spiritbox_fw/hal/icons/mic_disabled.png")
responseIcon = Image.open("./ghostsnstuff_spiritbox_fw/hal/icons/response.png")
responseDisabledIcon = Image.open("./ghostsnstuff_spiritbox_fw/hal/icons/response_disabled.png")
noResponseIcon = Image.open("./ghostsnstuff_spiritbox_fw/hal/icons/no_response.png")
noResponseDisabledIcon = Image.open("./ghostsnstuff_spiritbox_fw/hal/icons/no_response_disabled.png")
thinkingIcon = Image.open("./ghostsnstuff_spiritbox_fw/hal/icons/thinking.png")
thinkingDisabledIcon = Image.open("./ghostsnstuff_spiritbox_fw/hal/icons/thinking_disabled.png")
_micActive = False
_responseActive = False
_noResponseActive = False
_thinkingActive = False

def _tkDisplay():
    import PIL
    import tkinter as tk
    global root, tklabel
    root = tk.Tk()
    root.geometry("160x80")
    root.title("GHOSTSNSTUFF-SPIRITBOX WINDISP")
    bufferTK = ImageTk.PhotoImage(img)
    tklabel = tk.Label(root, image=bufferTK)
    tklabel.pack()
    root.mainloop()

if (isOnWin()):

    tkThread = threading.Thread(target=_tkDisplay)  
    def _pushBuffer(buffer):
        global bufferTK
        bufferTK = ImageTk.PhotoImage(buffer)
        tklabel.config(image=bufferTK)
        tklabel.pack()
    tkThread.start()
_glitch_kill_event = threading.Event()
def _glitchThread():
    while True:
        global _micActive
        _micActive = bool(random.getrandbits(1))
        global _thinkingActive
        _thinkingActive = bool(random.getrandbits(1))
        global _noResponseActive
        _noResponseActive = bool(random.getrandbits(1))
        global _responseActive
        _responseActive = bool(random.getrandbits(1))
        if isOnPi():
            if (bool(random.getrandbits(1))==True):
                disp.set_backlight(255)
            else:
                disp.set_backlight(255)
        if _glitch_kill_event.is_set():
            _micActive = False
            _thinkingActive = False
            _noResponseActive = False
            _responseActive = False
            return
        time.sleep(0.05)

def _dispThread():
    previousMillis = 0
    frequency = 65
    advanceDirection = 0.1
    while True:
        imgbuf = Image.new('RGB', (160, 80), color=(248, 133, 18))
        draw = ImageDraw.Draw(imgbuf)
        if time.time() - previousMillis >= 0.1:
            #advance sweep
            frequency = frequency + advanceDirection
            if frequency > 108:
                frequency = 108
                advanceDirection = -0.1
            if frequency < 65:
                frequency = 65
                advanceDirection = 0.1
            previousMillis = time.time()
        if frequency < 100:
            
            freqtext = "    "+str(round(frequency, 1))+" FM"
        else:
            
            freqtext = str(round(frequency, 1))+" FM"
        draw.text((3, 45), freqtext, (0, 0, 0), font)
            

        if _micActive == True:
            imgbuf.paste(micIcon, (3, 3))
        else:
            imgbuf.paste(micDisabledIcon, (3, 3))

        if _thinkingActive == True:
            imgbuf.paste(thinkingIcon, (26+6, 3))
        else:
            imgbuf.paste(thinkingDisabledIcon, (26+6, 3))

        if _noResponseActive == True:
            imgbuf.paste(noResponseIcon, (26+6+40+3, 3))
        else:
            imgbuf.paste(noResponseDisabledIcon, (26+6+40+3, 3))

        if _responseActive == True:
            imgbuf.paste(responseIcon, (26+6+40+3+40+3, 3))
        else:
            imgbuf.paste(responseDisabledIcon, (26+6+40+3+40+3, 3))
        
        
        #draw.text((3, 40), "196.6 FM", (0, 0 ,0), font)
        _pushBuffer(imgbuf)
        time.sleep(0.05)
dispGlitchThread = threading.Thread(target=_glitchThread)
def _dispBegin():
    dispMainThread = threading.Thread(target=_dispThread)
    dispMainThread.start()

class display(ABC):
    def begin(self, text):
        pass
    def printText(self, text):
        pass
    def micIcon(self, enable):
        pass
    def noResponseIcon(self, enable):
        pass
    def responseIcon(self, enable):
        pass
    def thinkingIcon(self, enable):
        pass
    def FMIcon(self, enable):
        pass
    def setBrightness(self, brightness):
        pass
    def glitch(self, enable):
        pass

class piDisplay(display):
    def begin(self):
        _dispBegin()
    def printText(self, text):
        draw = ImageDraw.Draw(img)
        #draw.rectangle((0, 20, 160, 40), (0, 0 ,0))
        #draw.rectangle((3, 3, 40, 40), (255, 255,255))
        
        img.paste(micDisabledIcon, (3, 3))
        img.paste(thinkingDisabledIcon, (26+6, 3))
        img.paste(noResponseIcon, (26+6+40+3, 3))
        img.paste(responseDisabledIcon, (26+6+40+3+40+3, 3))
        draw.text((3, 40), "196.6 FM", (0, 0, 0), font)
        _pushBuffer(img)
        #_pushBuffer(image)
    def micIcon(self ,enable):
        global _micActive
        _micActive = enable
    def noResponseIcon(self, enable):
        global _noResponseActive
        _noResponseActive = enable
    def responseIcon(self, enable):
        global _responseActive
        _responseActive = enable
    def thinkingIcon(self, enable):
        global _thinkingActive
        _thinkingActive = enable
    def glitch(self, enable):
        if enable == True:
            _glitch_kill_event.clear()
            dispGlitchThread.start()
        else:
            if dispGlitchThread.is_alive() and not _glitch_kill_event.is_set():
                _glitch_kill_event.set()

            


class consoleDisplay(display):
    def begin(self):
        pass
    def printText(self, text):
        print(f"display_large_text: {text}")
    def micIcon(self, enable):
        print(f"display_microphone_icon_enable: {enable}")
    def noResponseIcon(self, enable):
        print(f"display_no_response_icon_enable: {enable}")
    def responseIcon(self, enable):
        print(f"display_response_icon_enable: {enable}")
    def thinkingIcon(self, enable):
        print(f"display_thinking_icon_enable: {enable}")
    def FMIcon(self, enable):
        print(f"display_FM_icon_enable: {enable}")
    def setBrightness(self, brightness):
        print(f"display_brightness: {brightness}")

def getDisplay():
    if (isOnPi()):
        return piDisplay()
    elif (isOnWin()):
        global _win_display
        _win_display= True
        return piDisplay()
    else:
        return consoleDisplay()