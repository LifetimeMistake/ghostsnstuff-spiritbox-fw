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
scenario_file = "scenarios/scenario_2.json"
config.activity_grow_factor = 0.1
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
#emf_driver = EMFDriver()
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
    #emf_driver.glitch()
    if actions.glitch:
        #emf_driver.glitch()
        pass
    if not actions.speech:

        return
    if isinstance(actions.speech, list):
        buffers = tts.synthesize_batch(actions.speech, voice, 0.75)
        for word, buffer in zip(actions.speech, buffers):
            spk.playBuffer(buffer, 16000)
            disp.responseIcon(True)
            time.sleep(1)
            disp.printText(word)
            time.sleep(get_buffer_length(buffer, 16000, 1)-1)
            disp.responseIcon(False)
    else:
        buffer = tts.synthesize(actions.speech, voice, 0.75)
        spk.playBuffer(buffer, 16000)
        disp.responseIcon(True)
        time.sleep(0.5)
        disp.printText("XXXXXX")
        time.sleep(get_buffer_length(buffer, 16000, 1)-0.5)
        disp.responseIcon(False)


    

while True:
    disp.sweep(True)
    user_query = stt.transcribe(mic.awaitBuffer(), 16000)
    disp.thinkingIcon(True)
    turn_result = runtime.execute(user_query)
    disp.thinkingIcon(False)
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
        time.sleep(1)
        disp.noResponseIcon(False)
    
    # Act...