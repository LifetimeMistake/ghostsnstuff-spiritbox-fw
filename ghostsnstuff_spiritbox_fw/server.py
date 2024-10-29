import time
import random
import numpy as np
from openai import OpenAI
from pathlib import Path
from typing import Self, List
from .speech import STTClient, TTSClient, VOICE_MODELS
from .runtime import RuntimeConfig
from .hal.microphone import Microphone
from .hal.display import Display
from .hal.speaker import AudioDriver
from .hal.emf import EMFDriver
from .events import EventTimeline
from .agents import Writer
from .scenario import ScenarioDefinition, load_scenario
from .runtime import GameRuntime, SystemCallResult, GhostActions, GhostRole
from .utils import polish_to_english
from . import logging

class ServerConfig:
    primary_ghost_voice: VOICE_MODELS = "onyx"
    secondary_ghost_voice: VOICE_MODELS = "nova"
    voice_speed: float = 0.75
    tts_sample_rate: int = 16000
    base_scenarios_dir: Path = Path("./scenarios/")
    hint_buffer_min_length: float = 1.1
    hint_display_duration: float = 2.0
    interference_volume: float = 0.5

class Server:
    def __init__(self, client: OpenAI, mic: Microphone, display: Display, speaker: AudioDriver, emf: EMFDriver, timeline: EventTimeline, server_config: ServerConfig, runtime_config: RuntimeConfig) -> Self:
        self.client = client
        self.mic = mic
        self.display = display
        self.speaker = speaker
        self.emf = emf
        self.timeline = timeline
        self.server_config = server_config
        self.runtime_config = runtime_config
        self.current_scenario: ScenarioDefinition | None = None
        self.runtime: GameRuntime | None = None
        self.scenario_writer = Writer(
            client=client,
            model=runtime_config.curator_model,
            temperature=runtime_config.curator_temperature
        )
        self.tts_model = TTSClient(client)
        self.stt_client = STTClient(client)
        self._locked = False
        self._new_scenario = False
    
    def _reset_hardware(self):
        self.speaker.set_interference_level(0)
        self.speaker.set_interference_volume(self.server_config.interference_volume)
        self.display.enable_glitch(False)
        self.display.set_text(None)
        self.display.enable_sweep(False)
        self.emf.set_activity(1)
        
    def _enable_hardware(self):
        self.speaker.set_interference_level(1)
        self.display.enable_sweep(True)
        self.emf.set_activity(1)
        
    def _execute_glitch(self):
        self.display.enable_glitch(True)
        self.speaker.set_interference_level(2)
        self.emf.glitch()
        time.sleep(random.uniform(0.2, 0.5))
        self.speaker.set_interference_level(1)
        self.display.enable_glitch(False)
        
    def _play_ghost_speech(self, content: str, buffer: np.ndarray):
        self.display.set_icon_state(response=True)
        sound_length = self.speaker.play_buffer(buffer, self.server_config.tts_sample_rate)
        text = polish_to_english(content) if sound_length > self.server_config.hint_buffer_min_length else "SYSTEM ERROR"
        time.sleep(sound_length)
        self.display.set_text(text, duration=self.server_config.hint_display_duration)
        self.display.set_icon_state(response=False)
        
    def _execute_ghost_actions(self, actions: GhostActions, ghost: GhostRole):
        voice = (
            self.server_config.primary_ghost_voice if ghost == 'primary' 
            else self.server_config.secondary_ghost_voice
        )
        
        if actions.glitch:
            self._execute_glitch()
            
        if not actions.speech:
            return
        
        if isinstance(actions.speech, list):
            buffers = self.tts_model.synthesize_batch(actions.speech, voice, self.server_config.voice_speed)
            for word, buffer in zip(actions.speech, buffers):
                self._play_ghost_speech(word, buffer)
                time.sleep(random.uniform(0.5, 1.5))
        else:
            buffer = self.tts_model.synthesize(actions.speech, voice, self.server_config.voice_speed)
            self._play_ghost_speech("XXXXXX", buffer)
        
    def get_base_scenarios(self) -> List[Path]:
        scenario_files = list(self.server_config.base_scenarios_dir.glob("*.json"))
        return scenario_files
    
    def write_scenario(self, base_scenario: ScenarioDefinition | Path, prompt: str) -> ScenarioDefinition:
        if not isinstance(base_scenario, ScenarioDefinition):
            base_scenario = load_scenario(str(base_scenario.resolve()))
            
        response = self.scenario_writer.generate(
            prompt=prompt,
            scenario_type=base_scenario.scenario_type,
            scenario_example=base_scenario
        )
        
        logging.print(f"Writer has generated a new scenario. Model thoughts: {response.reasoning}")
        return response.scenario
    
    def start_scenario(self, scenario: ScenarioDefinition) -> bool:
        if self.current_scenario:
            logging.warn("Attempted to start a new scenario, but one is already running")
            return False
        
        self.current_scenario = scenario
        self.runtime = GameRuntime(
            client=self.client,
            scenario=scenario,
            config=self.runtime_config,
            timeline=self.timeline
        )
        self._new_scenario = True
        
        self._reset_hardware()
        self._enable_hardware()
        
        self.runtime.game_state.reset()
        logging.print("Scenario started")
        return True
    
    def stop_scenario(self):
        self.current_scenario = None
        self.runtime = None
        self._reset_hardware()
        logging.print("Scenario stopped")
        
    def execute_command(self, command: str) -> SystemCallResult | None:
        runtime = self.runtime
        if not runtime:
            return None
        
        return runtime.execute_command(command)