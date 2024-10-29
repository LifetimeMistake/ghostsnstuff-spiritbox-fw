import json
import time
import random
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from ghostsnstuff_spiritbox_fw.scenario import load_scenario
from ghostsnstuff_spiritbox_fw.events import EventTimeline
from ghostsnstuff_spiritbox_fw.runtime import GameRuntime, RuntimeConfig
from ghostsnstuff_spiritbox_fw.server import Server, ServerConfig
import ghostsnstuff_spiritbox_fw.logging as logging
from ghostsnstuff_spiritbox_fw.hal.emf import get_emf_driver
from ghostsnstuff_spiritbox_fw.hal.display import get_display
from ghostsnstuff_spiritbox_fw.hal.speaker import get_audio
from ghostsnstuff_spiritbox_fw.hal.microphone import get_microphone

load_dotenv()

client = OpenAI()
runtime_config = RuntimeConfig()
server_config = ServerConfig()
timeline = EventTimeline()
logging.set_timeline(timeline)

###### Configuration begins here
scenario_file = "scenarios/scenario_built.json"
scenario_prompt = "A group of ghost hunters is in Krośnica, a small village in Opole. They are trying to summon spirits of the dead. Unknowingly, they summon both a good and evil spirit. They must figure out which one to banish. Also, the group is polish speakers so while the scenario should be written in English, ghost details should be in Polish and they should also answer in Polish, same goes for the banishment rituals. They must be able to be spoken out loud in Polish."
runtime_config.activity_grow_factor = 0.15
###### Configuration ends here

###### Load scenario
base_scenario = load_scenario(scenario_file)

###### Initialize HAL
mic = get_microphone()
disp = get_display()
spk = get_audio()
emf = get_emf_driver()

def handle_mic_icon(enabled):
    disp.set_icon_state(mic=enabled)
mic.register_icon_callback(handle_mic_icon)

logging.print("Init OK")

###### Run server
server = Server(
    client=client,
    mic=mic,
    display=disp,
    speaker=spk,
    emf=emf,
    timeline=timeline,
    server_config=server_config,
    runtime_config=runtime_config
)

server.start_scenario(base_scenario)
server.mainloop()