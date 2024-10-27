import pygame
import numpy as np
import threading
import time
from scipy.signal import resample

class AudioDriver:
    def __init__(self, sample_rate: int = 44100, playback_channels: int = 4, enable_stereo: bool = True):
        self.sample_rate = sample_rate
        self.playback_channels = playback_channels
        self.enable_stereo = enable_stereo

        pygame.mixer.init(frequency=sample_rate, channels=2 if enable_stereo else 1)
        pygame.mixer.set_num_channels(playback_channels)
        pygame.mixer.set_reserved(1) # reserved for interference
        self.interference_sounds = [
            self.load_sound(f"./assets/sounds/interference_level{i}.wav") for i in range(1, 3)
        ]
        self.beeps = [
            self.load_sound(f"./assets/sounds/beep{i}.wav") for i in range(1, 4)
        ]
        self.interference_channel = pygame.mixer.Channel(0)

    def load_sound(self, path):
        """ Load a sound file and return the Sound object. """
        return pygame.mixer.Sound(path)

    def set_interference_level(self, level):
        """ Set the level of interference sound (0-2). """
        if level < 0 or level > 2:
            raise IndexError("Invalid interference level")
        
        if self.interference_channel.get_busy():
            self.interference_channel.stop()

        if level == 0:
            return

        interference = self.interference_sounds[level-1]
        self.interference_channel.play(interference, -1)

    def get_interference_volume(self) -> float:
        return self.interference_channel.get_volume()

    def set_interference_volume(self, volume: float):
        self.interference_channel.set_volume(volume)

    def play_beep(self, sound_index: int):
        """ Play a beep sound. """
        if sound_index < 0 or sound_index > 3:
            raise IndexError("Invalid beep index")
        
        sound = self.beeps[sound_index - 1]
        sound.play()
        return sound.get_length()

    def play_buffer(self, buffer, buffer_sample_rate):
        """ Play a numpy buffer as sound. """
        buffer = self.normalize_buffer(buffer, buffer_sample_rate)
        sound = pygame.mixer.Sound(buffer)
        sound.play()
        return sound.get_length()  # Return duration of the sound

    def normalize_buffer(self, buffer: np.ndarray, sample_rate: int):
        """ Normalize and adjust the numpy buffer to match Pygame's format. """
        # Resample if needed
        if sample_rate != self.sample_rate:
            num_samples = round(len(buffer) * self.sample_rate / sample_rate)
            buffer = resample(buffer, num_samples)
        
        # Normalize to int16 range
        max_val = np.max(np.abs(buffer))
        if max_val > 0:
            buffer = (buffer / max_val * 32767).astype(np.int16)  # Convert to int16

        # Convert to stereo if enabled
        if buffer.ndim == 1 and self.enable_stereo:
            buffer = np.column_stack((buffer, buffer))
        elif buffer.ndim > 2:
            raise ValueError("Audio buffer must be either mono or stereo")
        
        return buffer
    
def get_audio():
    return AudioDriver()