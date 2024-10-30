import time
import random
import numpy as np
from openai import OpenAI
from pathlib import Path
from typing import Self, List
from enum import Enum
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
    win_message: str = "Thank you..."
    lose_message: str = "You fool..."
    debug_api_enabled: bool = False
    debug_api_host: str = "0.0.0.0"
    debug_api_port: int = 8080
    debug_ui_enabled: bool = False
    debug_ui_port: int = 8090
    
class ExecutionState(Enum):
    INVALID_STATE = 0
    NORMAL = 1
    GAME_END = 2

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
        if server_config.debug_api_enabled:
            from .debug.api import DebugAPI
            self._debug_api = DebugAPI(
                server=self,
                host=server_config.debug_api_host,
                port=server_config.debug_api_port
            )
            self._debug_api.run()
        if server_config.debug_ui_enabled:
            if not server_config.debug_api_enabled:
                raise Exception("Debug UI requires the debug API to be enabled")
            
            # Wait for the debug API to init
            time.sleep(3)
            from .debug.ui_launcher import DebugUI
            self._debug_ui = DebugUI(port=server_config.debug_ui_port)
            self._debug_ui.start_server()
    
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
            
    def _game_won(self):
        self.speaker.set_interference_level(2)
        self.display.enable_glitch(True)
        self.emf.set_activity(6)
        time.sleep(5)
        for i in range(5):
            self.emf.set_activity(5 - i)
            time.sleep(random.uniform(0.7, 1))
        
        time.sleep(2)
        self.emf.set_activity(0)
        self.display.enable_glitch(False)
        self.display.enable_sweep(False)
        self.speaker.set_interference_level(0)
        time.sleep(3)
        self.display.set_text(self.server_config.win_message, duration=5)
        time.sleep(5)
        self.display.set_text(None)
        
    def _game_lost(self):
        buffer = self.tts_model.synthesize(self.server_config.lose_message, "onyx", 0.65)
        self.speaker.set_interference_level(3)
        time.sleep(1)
        self.emf.set_activity(6)
        time.sleep(0.5)
        audio_length = self.speaker.play_buffer(self.server_config.tts_sample_rate)
        time.sleep(audio_length + 1)
        self.display.enable_glitch(True)
        self.display.enable_sweep(False)
        
        for _ in range(random.randint(20, 40)):
            self.emf.glitch()
            time.sleep(random.uniform(0.05, 0.15))
            
        time.sleep(4)
        self.emf.set_activity(0)
        self.speaker.set_interference_level(0)
        self.display.enable_glitch(False)
        
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
    
    def get_timeline(self) -> EventTimeline:
        return self.timeline
    
    def get_current_scenario(self) -> ScenarioDefinition | None:
        return self.current_scenario
    
    def _execute(self) -> ExecutionState:
        scenario = self.current_scenario
        runtime = self.runtime
        if not scenario or not runtime:
            return ExecutionState.INVALID_STATE
        
        buffer = self.mic.await_buffer()
        self.display.set_icon_state(thinking=True)
        user_query = self.stt_client.transcribe(buffer, self.mic.get_sample_rate())
        logging.print(f"Detected speech: {user_query}")
        turn_result = runtime.execute(user_query)
        self.display.set_icon_state(thinking=False)
        
        if turn_result.game_result:
            if turn_result.game_result == "win":
                self._game_won()
            else:
                self._game_lost()
            return ExecutionState.GAME_END
        
        primary_actions = turn_result.primary_ghost_actions
        primary_has_content = primary_actions and primary_actions.speech
        secondary_actions = turn_result.secondary_ghost_actions
        secondary_has_content = secondary_actions and secondary_actions.speech
        
        primary_first = turn_result.ghost_order == "primary"
        if primary_first and primary_actions:
            self._execute_ghost_actions(primary_actions, "primary")
        if secondary_actions:
            self._execute_ghost_actions(secondary_actions, "secondary")
        if not primary_first and primary_actions:
            self._execute_ghost_actions(primary_actions, "primary")
            
        if not primary_has_content and not secondary_has_content:
            self.display.set_icon_state(no_response=True)
            time.sleep(2)
            self.display.set_icon_state(no_response=False)
            
        self.emf.set_activity(max(1, int(round(turn_result.activity_level / 2))))
        return ExecutionState.NORMAL
    
    def mainloop(self):
        if self._locked:
            raise Exception("Another thread is already executing the main loop")
        
        self._locked = True
        
        try:
            while True:
                executed = self._execute()
                if executed != ExecutionState.NORMAL:
                    time.sleep(1)
        finally:
            self._locked = False