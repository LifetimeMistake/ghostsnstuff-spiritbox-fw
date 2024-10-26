from abc import ABC
from . import platform
import threading
import time
import random

_win_display = False

if platform.isWindows():
    from PIL import Image, ImageDraw, ImageFont, ImageTk
    import tkinter as tk

if platform.isRaspberryPi():
    import st7735
    from PIL import Image, ImageDraw, ImageFont
    global disp
    disp = st7735.ST7735(port=0,cs=st7735.BG_SPI_CS_BACK,dc="GPIO9",backlight="GPIO12", rotation=90, spi_speed_hz=4000000)
    
    def _pushBuffer(buffer):
        disp.display(buffer)

img = Image.new('RGB', (160, 80), color=(248, 133, 18))
font = ImageFont.truetype("./assets/fonts/DSEG14Modern-Italic.ttf", 30)
micIcon = Image.open("./assets/icons/mic.png")
micDisabledIcon = Image.open("./assets/icons/mic_disabled.png")
responseIcon = Image.open("./assets/icons/response.png")
responseDisabledIcon = Image.open("./assets/icons/response_disabled.png")
noResponseIcon = Image.open("./assets/icons/no_response.png")
noResponseDisabledIcon = Image.open("./assets/icons/no_response_disabled.png")
thinkingIcon = Image.open("./assets/icons/thinking.png")
thinkingDisabledIcon = Image.open("./assets/icons/thinking_disabled.png")
_micActive = False
_responseActive = False
_noResponseActive = False
_thinkingActive = False
_sweep_enabled = False
_raw_text = ""
_text_string = ""

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

if (platform.isWindows()):

    tkThread = threading.Thread(target=_tkDisplay)  
    def _pushBuffer(buffer):
        global bufferTK
        bufferTK = ImageTk.PhotoImage(buffer)
        tklabel.config(image=bufferTK)
        tklabel.pack()
    tkThread.start()
_glitch_kill_event = threading.Event()
_scroll_kill_event = threading.Event()
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
        if platform.isRaspberryPi():
            if random.getrandbits(1):
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
        draw.text((3, 45), "~.~.~.~.~.~.", (194, 117, 40), font)
        if (_sweep_enabled == True):
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
                
                freqtext = "    "+str(round(frequency, 1))+"FM"
            else:
                
                freqtext = str(round(frequency, 1))+"FM"
            draw.text((3, 45), freqtext, (0, 0, 0), font)
        else:
            draw.text((3, 45), _text_string, (0, 0, 0), font)
            if (_text_string == ""):
                draw.text((3, 45), "----FM", (0, 0, 0), font)    

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

def _scrolling_text_thread():
    global _text_string
    text = _raw_text.replace(' ', '    ')
    scrollMillis = time.time()  # Initialize with the current time
    start = 0
    initial_wait = True  # Flag to handle the initial wait time
    global _sweep_enabled
    _sweep_enabled = False
    _text_string = text[0:6]

    while True:
        # Wait for 1 second at the start of scrolling
        if initial_wait and time.time() - scrollMillis >= 0.5:
            scrollMillis = time.time()  # Reset scrollMillis to the current time
            initial_wait = False  # Disable initial wait after the first run

        # Check if 0.2 seconds has passed for regular scrolling
        elif not initial_wait and time.time() - scrollMillis >= 0.10:
            # Calculate the end position
            end = start + 6
            if end > len(text):
                start = 0  # Reset to the beginning if the end exceeds the text length
                end = start + 6
                initial_wait = True  # Enable initial wait when restarting
                time.sleep(0.5)  # Wait for 0.5 seconds at the end

            # Update the global text string
            _text_string = text[start:end]
            #print(_text_string)  # Print the current segment

            # Update the start position for the next iteration
            start += 1

            # Update the scrollMillis to the current time
            scrollMillis = time.time()

        # Check if the kill event is set
        if _scroll_kill_event.is_set():
            _text_string = text[0:6]
            print("Scrolling stopped.")
            return

        # Sleep for a short time to prevent tight looping




def _dispBegin():
    dispMainThread = threading.Thread(target=_dispThread)
    dispMainThread.start()

class display(ABC):
    def begin(self, text):
        pass
    def sweep(self, enabled):
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
    def sweep(self, enabled):
        global _sweep_enabled

        _scroll_kill_event.set()
        global _text_string
        global _raw_text
        _text_string = ""
        _raw_text = ""
        _sweep_enabled = enabled
    def printText(self, text):
        # draw = ImageDraw.Draw(img)
        # #draw.rectangle((0, 20, 160, 40), (0, 0 ,0))
        # #draw.rectangle((3, 3, 40, 40), (255, 255,255))
        
        # img.paste(micDisabledIcon, (3, 3))
        # img.paste(thinkingDisabledIcon, (26+6, 3))
        # img.paste(noResponseIcon, (26+6+40+3, 3))
        # img.paste(responseDisabledIcon, (26+6+40+3+40+3, 3))
        # draw.text((3, 40), "196.6 FM", (0, 0, 0), font)
        # _pushBuffer(img)
        #_pushBuffer(image)
        _scroll_kill_event.set()
        time.sleep(0.1)
        dispScrollThread = threading.Thread(target=_scrolling_text_thread)
        if (not _scroll_kill_event.is_set):
            _scroll_kill_event.set()
            time.sleep(0.05)
            _scroll_kill_event.clear()
        else:
            _scroll_kill_event.clear()
        _scroll_kill_event.clear()
        global _raw_text
        _raw_text = text
        dispScrollThread.start()
        
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
        dispGlitchThread = threading.Thread(target=_glitchThread)
        if enable == True and not dispGlitchThread.is_alive():
            _glitch_kill_event.set()
            time.sleep(0.1)
            _glitch_kill_event.clear()
            #dispGlitchThread.start()
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
    if (platform.isRaspberryPi()):
        return piDisplay()
    elif (platform.isWindows()):
        global _win_display
        _win_display= True
        return piDisplay()
    else:
        return consoleDisplay()