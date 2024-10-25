from openai import OpenAI
from dotenv import load_dotenv
from ghostsnstuff_spiritbox_fw.agents import Writer
from ghostsnstuff_spiritbox_fw.scenario import ScenarioDefinition, load_scenario
from ghostsnstuff_spiritbox_fw.events import EventTimeline
from ghostsnstuff_spiritbox_fw.game import GameRuntime, RuntimeConfig
import ghostsnstuff_spiritbox_fw.logging as logging
from ghostsnstuff_spiritbox_fw.speech import STTClient
import json

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

###### Initialize HAL
#emf_driver = EMFDriver()
disp = getDisplay()
spk = getSpeaker()
mic = getMic()

logging.print("Init OK")
logging.print("Starting scenario")

###### Run main loop
runtime.game_state.reset()
print(stt.transcribe(mic.awaitBuffer(), 16000))
while True:
    
    user_query = "..."
    turn_result = runtime.execute(user_query)
    # Act...