from abc import ABC, abstractmethod
import threading
import time
import random
from PIL import Image, ImageDraw, ImageFont
from .. import logging
from . import platform
from ..utils import clamp

FONT_PATH = "./assets/fonts/DSEG14Modern-Italic.ttf"
ICON_PATHS = {
    "mic": "./assets/icons/mic.png",
    "mic_disabled": "./assets/icons/mic_disabled.png",
    "response": "./assets/icons/response.png",
    "response_disabled": "./assets/icons/response_disabled.png",
    "no_response": "./assets/icons/no_response.png",
    "no_response_disabled": "./assets/icons/no_response_disabled.png",
    "thinking": "./assets/icons/thinking.png",
    "thinking_disabled": "./assets/icons/thinking_disabled.png",
}
DISPLAY_REFRESH_INTERVAL = 0.05

# Initialize icons
icons = {name: Image.open(path) for name, path in ICON_PATHS.items()}

try:
    import tkinter as tk
    from PIL import ImageTk
    TK_AVAILABLE = True
except ImportError:
    TK_AVAILABLE = False

try:
    import st7735
    ST7735_AVAILABLE = True
    ST7735_PORT = 0
    ST7735_CS = st7735.BG_SPI_CS_BACK
    ST7735_DC = "GPIO9"
    ST7735_BACKLIGHT = "GPIO12"
    ST7735_ROTATION = 90
    ST7735_SPI_SPEED_HZ = 4000000
except ImportError:
    ST7735_AVAILABLE = False
    
def calculate_text_offset(
    text_length: int, 
    display_width: int, 
    current_tick: int, 
    start_delay_seconds: float, 
    display_duration: float | None, 
    max_scroll_duration: float = 5,
):
    # Calculate parameters
    initial_delay_ticks = int(start_delay_seconds / DISPLAY_REFRESH_INTERVAL)  # delay before scrolling starts
    scroll_duration_ticks = int(max_scroll_duration / DISPLAY_REFRESH_INTERVAL)  # max scroll duration in ticks

    # Limit scroll duration if a shorter display duration is set
    if display_duration is not None:
        scroll_duration_ticks = min(scroll_duration_ticks, int(display_duration / DISPLAY_REFRESH_INTERVAL) - 2 * initial_delay_ticks)
    
    # Scroll only if text length exceeds display width
    if text_length <= display_width:
        return 0  # no scrolling needed
    
    # Calculate total scrollable distance
    max_offset = text_length - display_width  # max characters to scroll

    # Determine the effective tick count with delay applied for each interval
    effective_t = current_tick % (scroll_duration_ticks + 2 * initial_delay_ticks)
    
    # Direction: 0 = forward, 1 = reverse, alternates each interval
    interval_count = current_tick // (scroll_duration_ticks + 2 * initial_delay_ticks)
    direction = interval_count % 2

    # Apply delays at the start and end of each interval
    if effective_t < initial_delay_ticks:
        return 0 if direction == 0 else max_offset  # Starting delay
    elif effective_t >= initial_delay_ticks + scroll_duration_ticks:
        return max_offset if direction == 0 else 0  # Ending delay

    # Calculate scroll progress within the scrolling portion of the interval
    progress_in_interval = effective_t - initial_delay_ticks
    step_fraction = progress_in_interval / scroll_duration_ticks

    # Offset based on direction and step fraction
    offset = round(max_offset * step_fraction)
    return offset if direction == 0 else max_offset - offset


class DisplayRenderer:
    def __init__(self):
        # Shared display assets
        self.font = ImageFont.truetype("./assets/fonts/DSEG14Modern-Italic.ttf", 30)
        self.icons = {
            "mic": (icons["mic"], icons["mic_disabled"]),
            "response": (icons["response"], icons["response_disabled"]),
            "no_response": (icons["no_response"], icons["no_response_disabled"]),
            "thinking": (icons["thinking"], icons["thinking_disabled"]),
        }

    def render(self, display: 'Display'):
        # Creates a single frame for the display
        imgbuf = Image.new('RGB', (160, 80), color=(248, 133, 18))
        draw = ImageDraw.Draw(imgbuf)

        # Draw sweep or text
        if display._glitch_enabled:
            self._draw_glitch(imgbuf, draw)
        elif display._text:
            offset = calculate_text_offset(
                text_length=len(display._text),
                display_width=6,
                current_tick=display._text_ticks,
                start_delay_seconds=0.5,
                display_duration=display._text_duration * DISPLAY_REFRESH_INTERVAL 
                if display._text_duration else None,
                max_scroll_duration=5.0
            )
            self._draw_text(draw, display._text, offset)
        elif display._sweep_enabled:
            self._draw_sweep(draw, display._sweep_value)

        # Draw icons
        if not display._glitch_enabled:
            self._draw_icons(
                imgbuf=imgbuf,
                mic_active=display._mic_active,
                thinking_active=display._thinking_active,
                no_response_active=display._no_response_active,
                response_active=display._response_active,
            )

        return imgbuf

    def _draw_glitch(self, imgbuf: Image.Image, draw: ImageDraw.ImageDraw):
        self._draw_icons(
            imgbuf=imgbuf,
            mic_active=bool(random.getrandbits(1)),
            no_response_active=bool(random.getrandbits(1)),
            response_active=bool(random.getrandbits(1)),
            thinking_active=bool(random.getrandbits(1))
        )

        text = "".join([random.choice(['~', '-', 'X', '?', '+', 'F', 'M', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']) for _ in range(6)])
        self._draw_text(draw, text, 0)

    def _draw_sweep(self, draw: ImageDraw.ImageDraw, frequency: float):
        freq_text = f"{frequency:.1f} FM" if frequency >= 100 else f"    {frequency:.1f} FM"
        draw.text((3, 45), freq_text, (0, 0, 0), self.font)

    def _draw_text(self, draw: ImageDraw.ImageDraw, text: str, offset: int):
        text_to_display = text[offset:offset+6] if text else "----FM"
        draw.text((3, 45), text_to_display, (0, 0, 0), self.font)

    def _draw_icons(self, imgbuf: Image.Image, mic_active: bool, thinking_active: bool, no_response_active: bool, response_active: bool):
        positions = [(3, 3), (32, 3), (72, 3), (112, 3)]
        icons = ["mic", "thinking", "no_response", "response"]
        states = [mic_active, thinking_active, no_response_active, response_active]

        for pos, icon, active in zip(positions, icons, states):
            imgbuf.paste(self.icons[icon][0] if active else self.icons[icon][1], pos)

class Display(ABC):
    def __init__(self):
        self._mic_active = False
        self._response_active = False
        self._no_response_active = False
        self._thinking_active = False
        self._sweep_value = False
        self._sweep_forward = True
        self._sweep_enabled = False
        self._glitch_enabled = False
        self._text = None
        self._text_ticks = None
        self._text_duration = None
        self._update_thread = threading.Thread(target=self._update_loop, daemon=True)

    @abstractmethod
    def begin(self):
        self._update_thread.start()

    def enable_sweep(self, enable: bool):
        self._sweep_enabled = enable

    def set_icon_state(self, mic: bool | None = None, response: bool | None = None, no_response: bool | None = None, thinking: bool | None = None):
        self._mic_active = mic if mic is not None else self._mic_active
        self._response_active = response if response is not None else self._response_active
        self._no_response_active = no_response if no_response is not None else self._no_response_active
        self._thinking_active = thinking if thinking is not None else self._thinking_active

    def enable_glitch(self, enable: bool):
        self._glitch_enabled = enable

    def set_text(self, content: str | None, duration: float | None = None):
        if content:
            self._text = content.replace(" ", "    ")
            self._text_ticks = 0
            self._text_duration = int(duration / DISPLAY_REFRESH_INTERVAL) if duration else None
        else:
            self._text = None
            self._text_ticks = None
            self._text_duration = None

    @abstractmethod
    def _render(self):
        pass

    def _update_loop(self):
        while True:
            self._render()

            # Update sweep frequency
            if self._sweep_enabled:
                sweep_factor = 0.1 if self._sweep_forward else -0.1
                sweep_value = clamp(round(self._sweep_value + sweep_factor, 1), 63, 108)
                if sweep_value == 63 or sweep_value == 108:
                    self._sweep_forward = not self._sweep_forward

                self._sweep_value = sweep_value

            if self._text:
                self._text_ticks += 1
                # Disable text after a while if it's supposed to be temporary
                if self._text_duration and self._text_ticks > self._text_duration:
                    self._text = None
                    self._text_ticks = None
                    self._text_duration = None

            time.sleep(DISPLAY_REFRESH_INTERVAL)

class WindowsDisplay(Display):
    def __init__(self):
        super().__init__()
        self.renderer = DisplayRenderer()
        self.root = None
        self._display_thread = threading.Thread(target=self._run_display, daemon=True)

    def begin(self):
        self._display_thread.start()
        super().begin()

    def _run_display(self):
        self.root = tk.Tk()
        self.root.geometry("160x80")
        self.root.title("GHOSTSNSTUFF-SPIRITBOX WINDISP")
        self.tklabel = tk.Label(self.root)
        self.tklabel.pack()
        self.root.mainloop()

    def _render(self):
        if not self.root:
            return
        
        buffer = ImageTk.PhotoImage(self.renderer.render(self))
        self.tklabel.config(image=buffer)
        self.tklabel.image = buffer

class ST7735Display(Display):
    def __init__(self):
        super().__init__()
        self.renderer = DisplayRenderer()
        self.display = st7735.ST7735(
            port=ST7735_PORT,
            cs=ST7735_CS,
            dc=ST7735_DC,
            backlight=ST7735_BACKLIGHT,
            rotation=ST7735_ROTATION,
            spi_speed_hz=ST7735_SPI_SPEED_HZ
        )

    def begin(self):
        return super().begin()
    
    def _render(self):
        buffer = self._render()
        self.display.display(buffer)

class ConsoleDisplay(Display):
    def __init__(self):
        super().__init__()

    def begin(self):
        pass

    def enable_sweep(self, enable):
        super().enable_sweep(enable)
        logging.print(f"Display: Sweep enabled = {enable}")

    def set_icon_state(self, mic = None, response = None, no_response = None, thinking = None):
        super().set_icon_state(mic, response, no_response, thinking)
        if mic is not None:
            logging.print(f"Display: Microphone icon = {mic}")
        if response is not None:
            logging.print(f"Display: Response icon = {response}")
        if no_response is not None:
            logging.print(f"Display: No response icon = {no_response}")
        if thinking is not None:
            logging.print(f"Display: Thinking icon = {thinking}")

    def enable_glitch(self, enable):
        super().enable_glitch(enable)
        logging.print(f"Display: Glitch enabled = {enable}")

    def set_text(self, content, duration = None):
        super().set_text(content, duration)     
        logging.print(f"Display: Set text: {content}, duration: {duration}")

def get_display():
    if platform.isWindows():
        if TK_AVAILABLE:
            return WindowsDisplay()
        else:
            logging.warn("Detected Windows platform, but tkinter was not available")
    
    if platform.isRaspberryPi():
        if ST7735_AVAILABLE:
            return ST7735Display()
        else:
            logging.warn("Detected Raspberry Pi platform, but st7735 was not available")

    return ConsoleDisplay()