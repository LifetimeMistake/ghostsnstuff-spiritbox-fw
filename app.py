from openai import OpenAI
from dotenv import load_dotenv
from ghostsnstuff_spiritbox_fw.agents import Writer
from ghostsnstuff_spiritbox_fw.scenario import ScenarioDefinition, load_scenario
from ghostsnstuff_spiritbox_fw.events import EventTimeline
from ghostsnstuff_spiritbox_fw.game import GameRuntime, RuntimeConfig
import ghostsnstuff_spiritbox_fw.logging as logging
from ghostsnstuff_spiritbox_fw.speech import STTClient, TTSClient
import json
import time

from ghostsnstuff_spiritbox_fw.hal.emf import EMFDriver
from ghostsnstuff_spiritbox_fw.hal.display import getDisplay
from ghostsnstuff_spiritbox_fw.hal.speaker import getSpeaker
from ghostsnstuff_spiritbox_fw.hal.microphone import getMic

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
emf = EMFDriver()
disp = getDisplay()
spk = getSpeaker()
mic = getMic()

disp.begin()
mic.registerIconCallback(disp.micIcon)

logging.print("Init OK")
logging.print("Starting scenario")

###### Run main loop
runtime.game_state.reset()

PRIMARY_GHOST_VOICE = "onyx"
SECONDARY_GHOST_VOICE = "nova"
VOICE_SPEED = 0.75

def get_buffer_length(buffer, sample_rate, num_channels):
    num_samples = buffer.size
    return num_samples / (sample_rate*num_channels)

def handle_ghost_actions(actions, voice):
    emf.glitch()
    if actions.glitch:
        spk.setInterference(3)
        emf.glitch()
        disp.glitch(True)
        time.sleep(0.5)
        disp.glitch(False)
        spk.setInterference(1)
        pass
    if not actions.speech:

        return
    if isinstance(actions.speech, list):
        buffers = tts.synthesize_batch(actions.speech, voice, 0.75)
        for word, buffer in zip(actions.speech, buffers):
            spk.playBuffer(buffer, 16000)
            disp.responseIcon(True)
            time.sleep(1.5)
            disp.printText(word)
            time.sleep(get_buffer_length(buffer, 16000, 1)-1.5)
            disp.responseIcon(False)
    else:
        buffer = tts.synthesize(actions.speech, voice, 0.75)
        spk.playBuffer(buffer, 16000)
        disp.responseIcon(True)
        time.sleep(1)
        disp.printText("XXXXXX")
        time.sleep(get_buffer_length(buffer, 16000, 1)-1)
        disp.responseIcon(False)

def win_condition():
    spk.setInterference(3)
    emf.set_activity(6)
    time.sleep(5)
    for i in range(5):
        emf.set_activity(5 - i)
        time.sleep(1)

    emf.set_activity(0)
    spk.setInterference(0)
    disp.sweep(False)
    time.sleep(3)
    disp.printText("Thank you")
    time.sleep(5)
    disp.sweep(False)
    return

def lose_condition():
    buffer = tts.synthesize("Głupcze...", "onyx", 0.5)
    spk.setInterference(3)
    emf.set_activity(6)
    time.sleep(2)
    disp.glitch(True)
    for i in range(30):
        emf.glitch()
        time.sleep(0.1)

    time.sleep(2)
    spk.playBuffer(buffer, 16000)
    time.sleep(3)
    disp.sweep(False)
    emf.set_activity(0)
    spk.setInterference(0)

while True:
    disp.sweep(True)
    user_query = stt.transcribe(mic.awaitBuffer(), 16000)
    disp.thinkingIcon(True)
    turn_result = runtime.execute(user_query)
    disp.thinkingIcon(False)

    if turn_result.game_result:
        if turn_result.game_result == "win":
            win_condition()
        else:
            lose_condition()
        
        break

    if turn_result.ghost_order == "primary":
        if turn_result.primary_ghost_actions:
            handle_ghost_actions(turn_result.primary_ghost_actions, PRIMARY_GHOST_VOICE)
        if turn_result.secondary_ghost_actions:
            handle_ghost_actions(turn_result.secondary_ghost_actions, SECONDARY_GHOST_VOICE)
    else:
        if turn_result.secondary_ghost_actions:
            handle_ghost_actions(turn_result.secondary_ghost_actions, SECONDARY_GHOST_VOICE)
        if turn_result.primary_ghost_actions:
            handle_ghost_actions(turn_result.primary_ghost_actions, PRIMARY_GHOST_VOICE)
    
    if not turn_result.ghost_order == "primary" and turn_result.ghost_order == "secondary":
        disp.noResponseIcon(True)
        time.sleep(2)
        disp.noResponseIcon(False)

    emf.set_activity(max(1, int(round(turn_result.activity_level / 2))))