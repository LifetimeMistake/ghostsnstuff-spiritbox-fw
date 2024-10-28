from openai import OpenAI
from dotenv import load_dotenv
from ghostsnstuff_spiritbox_fw.agents import Writer
from ghostsnstuff_spiritbox_fw.scenario import ScenarioDefinition, load_scenario
from ghostsnstuff_spiritbox_fw.events import EventTimeline
from ghostsnstuff_spiritbox_fw.game import GameRuntime, RuntimeConfig, GhostActions, RuntimeExecutionResult
import ghostsnstuff_spiritbox_fw.logging as logging
from ghostsnstuff_spiritbox_fw.speech import STTClient, TTSClient, VOICE_MODELS
import json
import time
import random
import numpy as np

from ghostsnstuff_spiritbox_fw.hal.emf import get_emf_driver
from ghostsnstuff_spiritbox_fw.hal.display import get_display
from ghostsnstuff_spiritbox_fw.hal.speaker import get_audio
from ghostsnstuff_spiritbox_fw.hal.microphone import get_microphone

load_dotenv()

client = OpenAI()
config = RuntimeConfig()
timeline = EventTimeline()
logging.set_timeline(timeline)

###### Configuration begins here
scenario_file = "scenarios/scenario_built.json"
scenario_prompt = "A group of ghost hunters is in Krośnica, a small village in Opole. They are trying to summon spirits of the dead. Unknowingly, they summon both a good and evil spirit. They must figure out which one to banish. Also, the group is polish speakers so while the scenario should be written in English, ghost details should be in Polish and they should also answer in Polish, same goes for the banishment rituals. They must be able to be spoken out loud in Polish."
config.activity_grow_factor = 0.15
###### Configuration ends here

###### Initialize runtime
writer = Writer(
    client=client,
    model=config.curator_model,
    temperature=config.curator_temperature
)

base_scenario = load_scenario(scenario_file)
runtime = GameRuntime(
    client=client,
    scenario=base_scenario,
    config=config,
    timeline=timeline
)
stt = STTClient(client)
tts = TTSClient(client)

###### Initialize HAL
emf = get_emf_driver()
disp = get_display()
spk = get_audio()
mic = get_microphone()

disp.begin()
disp.enable_sweep(True)
spk.set_interference_volume(0.5)
spk.set_interference_level(1)

def handle_mic_icon(enabled):
    disp.set_icon_state(mic=enabled)
mic.register_icon_callback(handle_mic_icon)

logging.print("Init OK")
logging.print("Starting scenario")

###### Run main loop

PRIMARY_GHOST_VOICE = "onyx"
SECONDARY_GHOST_VOICE = "nova"
VOICE_SPEED = 0.75
TTS_SAMPLE_RATE = 16000

def polish_to_english(text):
    polishenglish = str.maketrans(
        "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ",
        "acelnoszzACELNOSZZ"
    )
    return text.translate(polishenglish)

def execute_glitch():
    disp.enable_glitch(True)
    spk.set_interference_level(2)
    emf.glitch()
    time.sleep(0.5)
    spk.set_interference_level(1)
    disp.enable_glitch(False)

def play_ghost_speech(content: str, buffer: np.ndarray):
    disp.set_icon_state(response=True)

    sound_length = spk.play_buffer(buffer, TTS_SAMPLE_RATE)
    text = polish_to_english(content) if sound_length > 1.1 else "SYSTEM ERROR"
    time.sleep(sound_length)
    disp.set_text(text, duration=2)
    disp.set_icon_state(response=False)

    time.sleep(random.uniform(0.5, 1.5))

def handle_ghost_actions(actions: GhostActions, voice: VOICE_MODELS):
    if actions.glitch:
        execute_glitch()

    if not actions.speech:
        return
    
    if isinstance(actions.speech, list):
        buffers = tts.synthesize_batch(actions.speech, voice, VOICE_SPEED)
        for word, buffer in zip(actions.speech, buffers):
            word = word.strip()
            if not word.endswith("..."):
                word = f"{word}..."

            play_ghost_speech(word, buffer)
    else:
        buffer = tts.synthesize(actions.speech, voice, VOICE_SPEED)
        play_ghost_speech("XXXXXX", buffer)

def win_condition():
    spk.set_interference_level(3)
    disp.enable_glitch(True)
    emf.set_activity(6)
    time.sleep(5)
    for i in range(5):
        emf.set_activity(5 - i)
        time.sleep(1)
    time.sleep(2)
    emf.set_activity(0)
    disp.enable_glitch(False)
    spk.set_interference_level(0)
    disp.enable_sweep(False)
    time.sleep(3)
    disp.set_text("Thank you", duration=5)
    time.sleep(5)
    disp.set_text(None)
    return

def lose_condition():
    buffer = tts.synthesize("Głupcze...", "onyx", 0.5)
    spk.set_interference_level(3)
    time.sleep(1)
    emf.set_activity(6)
    time.sleep(0.5)
    spk.play_buffer(buffer, TTS_SAMPLE_RATE)
    time.sleep(2)
    disp.enable_glitch(True)
    disp.enable_sweep(False)

    for _ in range(30):
        emf.glitch()
        time.sleep(0.1)

    time.sleep(4)
    emf.set_activity(0)
    spk.set_interference_level(0)
    disp.enable_glitch(False)

runtime.game_state.set_activity_level(3)

while True:
    buffer = mic.await_buffer()
    disp.set_icon_state(thinking=True)
    user_query = stt.transcribe(buffer, mic.get_sample_rate())
    print(user_query)
    turn_result = runtime.execute(user_query)
    disp.set_icon_state(thinking=False)

    if turn_result.game_result:
        if turn_result.game_result == "win":
            win_condition()
        else:
            lose_condition()
        break

    primary_actions = turn_result.primary_ghost_actions
    primary_has_content = primary_actions and primary_actions.speech
    secondary_actions = turn_result.secondary_ghost_actions
    secondary_has_content = secondary_actions and secondary_actions.speech

    if turn_result.ghost_order == "primary":
        if primary_actions:
            handle_ghost_actions(primary_actions, PRIMARY_GHOST_VOICE)
        if secondary_actions:
            handle_ghost_actions(secondary_actions, SECONDARY_GHOST_VOICE)
    else:
        if secondary_actions:
            handle_ghost_actions(secondary_actions, SECONDARY_GHOST_VOICE)
        if primary_actions:
            handle_ghost_actions(primary_actions, PRIMARY_GHOST_VOICE)
    
    if not primary_has_content and not secondary_has_content:
        disp.set_icon_state(no_response=True)
        time.sleep(2)
        disp.set_icon_state(no_response=False)

    emf.set_activity(max(1, int(round(turn_result.activity_level / 2))))