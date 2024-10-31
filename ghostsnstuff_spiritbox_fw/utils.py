import io
import random
import numpy as np
import soundfile as sf
from scipy.io.wavfile import write
from scipy.signal import butter, filtfilt, resample
from . import logging


def clamp(n, minimum, maximum):
    return max(minimum, min(n, maximum))

def weighted_ghost_choice(activity_level):
    primary_weight = 0
    secondary_weight = 0
    both_weight = 0

    if activity_level <= 3:
        # At levels 1-3, only primary ghost is active
        primary_weight = 10
    elif activity_level == 4:
        # At level 4, the secondary ghost becomes an option
        primary_weight = 8
        secondary_weight = 2
    elif activity_level == 5:
        # At level 5, secondary gains more presence
        primary_weight = 7
        secondary_weight = 3
    elif activity_level == 6:
        # At level 6, we aim for a 60% primary, 40% secondary split
        primary_weight = 6
        secondary_weight = 4
    elif activity_level == 7:
        # At level 7, we aim for a 50/50 split
        primary_weight = 5
        secondary_weight = 5
    elif activity_level == 8:
        # At level 8, we introduce both with 30% primary, 30% secondary, 40% both
        primary_weight = 3
        secondary_weight = 3
        both_weight = 4
    elif activity_level == 9:
        # At level 9, 20% primary, 20% secondary, 60% both
        primary_weight = 2
        secondary_weight = 2
        both_weight = 6
    elif activity_level == 10:
        # At level 10, 5% primary, 5% secondary, 90% both
        primary_weight = 0.5
        secondary_weight = 0.5
        both_weight = 9

    # Create a list of options and corresponding weights
    options = ["primary", "secondary", "both"]
    weights = [primary_weight, secondary_weight, both_weight]

    # Normalize weights to ensure valid distribution
    total_weight = sum(weights)
    if total_weight == 0:
        return "primary"

    # Choose based on the weighted distribution
    return random.choices(options, weights=weights, k=1)[0]

def sanitize_ghost_speech(content: list[str] | str, word_limit: int = 5) -> list[str] | str:
    def sanitize_word(word: str) -> str:
        # If the word is actually a sentence, return the longest word from that sentence
        if " " in word:
            logging.warn(f"Fixing bad word '{word}'")
            subwords = word.split(" ")
            return max(subwords, key=len).upper()  # Return the longest subword in uppercase
        return word.upper()

    if isinstance(content, str):
        words = content.split(" ")
        if len(words) > word_limit:
            logging.warn(f"Trimming sentence: {len(words)}->{word_limit} words")
        return " ".join([sanitize_word(w) for w in words[:word_limit]])

    else:
        sanitized_words = []
        for word in content:
            sanitized_words.append(sanitize_word(word))
        if len(sanitized_words) > word_limit:
            logging.warn(f"Trimming word list: {len(sanitized_words)}->{word_limit} words")
        return sanitized_words[:word_limit]
    
def polish_to_english(text):
    polishenglish = str.maketrans(
        "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ",
        "acelnoszzACELNOSZZ"
    )
    return text.translate(polishenglish)

def numpy_to_wav(buffer, sample_rate):
    pcm_int16 = np.int16(buffer * 32767)
    memory_buffer = io.BytesIO()
    sf.write(memory_buffer, buffer, sample_rate, format='WAV', subtype='FLOAT')
    memory_buffer.seek(0)
    return memory_buffer

def bit_reduction(audio, bit_depth=8, mix=0.7):
    factor = 2 ** (16 - bit_depth)
    degraded_audio = np.round(audio * factor) / factor
    return mix * audio + (1 - mix) * degraded_audio

def sample_rate_reduction(audio, original_rate, target_rate, mix=0.7):
    reduced_audio = resample(audio, int(len(audio) * target_rate / original_rate))
    upsampled_audio = resample(reduced_audio, len(audio))
    return mix * audio + (1 - mix) * upsampled_audio

def bandpass_filter(audio, lowcut, highcut, sample_rate, order=5):
    nyquist = 0.5 * sample_rate
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = butter(order, [low, high], btype="band")
    return filtfilt(b, a, audio)

def amplitude_modulation(audio, sample_rate, mod_freq=2, depth=0.3):
    t = np.arange(len(audio)) / sample_rate
    modulation = 1 - depth * (1 + np.sin(2 * np.pi * mod_freq * t)) / 2
    return audio * modulation

def add_noise(audio, noise_level=0.01):
    noise = np.random.normal(0, noise_level, audio.shape)
    return audio + noise

import numpy as np

def random_dropouts(audio, dropout_rate=0.1, dropout_length=0.05, sample_rate=44100):
    total_samples = len(audio)
    dropout_samples = int(dropout_length * sample_rate)  # Duration of each dropout in samples
    
    for i in range(0, total_samples, int(sample_rate * 2)):  # Introduce dropouts every ~2 seconds
        if np.random.rand() < dropout_rate:
            start = i
            end = min(i + dropout_samples, total_samples)
            audio[start:end] = 0  # Mute this segment
    return audio

def variable_noise(audio, sample_rate, base_noise=0.00001, max_noise=0.01, change_rate=0.1):
    total_samples = len(audio)
    noise = np.random.normal(0, base_noise, total_samples)  # Start with base noise
    
    # Introduce random increases in noise level
    for i in range(0, total_samples, int(0.5 * sample_rate)):  # Adjust every half-second
        if np.random.rand() < change_rate:
            noise_level = np.random.uniform(base_noise, max_noise)
            noise[i:i + int(0.5 * sample_rate)] = np.random.normal(0, noise_level, int(0.5 * sample_rate))
    return audio + noise


def haunted_effect(audio, sample_rate):
    # Apply each effect with a light touch
    audio = bit_reduction(audio, bit_depth=5, mix=0.8)
    audio = sample_rate_reduction(audio, sample_rate, 8000, mix=0.8)
    audio = bandpass_filter(audio, 300, 3000, sample_rate)
    audio = amplitude_modulation(audio, sample_rate, mod_freq=2, depth=0.2)
    audio = add_noise(audio, noise_level=0.00001)
    
    # Add random dropouts and variable noise
    audio = random_dropouts(audio, dropout_rate=0.2, dropout_length=0.05, sample_rate=sample_rate)    
    return np.clip(audio, -1.0, 1.0)  # Ensure the signal stays within [-1.0, 1.0]
