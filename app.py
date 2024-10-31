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
runtime_config.activity_grow_factor = 0.15
server_config.debug_api_enabled = True
server_config.debug_ui_enabled = True
server_config.voice_speed = 1
runtime_config.initial_activity_level = 1
###### Configuration ends here

###### Initialize HAL
mic = get_microphone()
disp = get_display()
spk = get_audio()
emf = get_emf_driver()

disp.begin()

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

server.mainloop()