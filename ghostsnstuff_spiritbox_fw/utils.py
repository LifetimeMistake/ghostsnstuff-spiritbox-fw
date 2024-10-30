import random
import numpy as np
from scipy.io.wavfile import write
import io
import soundfile as sf
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
    with open("output.wav", "wb") as f:
        f.write(memory_buffer.read())
    return memory_buffer