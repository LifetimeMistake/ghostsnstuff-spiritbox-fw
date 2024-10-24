from openai import OpenAI
from typing import Self, Optional
from .scenario import ScenarioDefinition
from .models.curator import CuratorNotes
from .models.state import GameState
from .agents import Curator, Ghost
from .conversation import Conversation

class RuntimeConfig:
    curator_model: str = "gpt-4o-mini"
    ghost_model: str = "gpt-4o-mini"
    curator_temperature: float = 0.2
    ghost_temperature: float = 0.5
    initial_activity_level: float = 1.0
    timer_value: Optional[float] = 900.0
    activity_grow_factor: float = 0.1
    glitch_min_level: float = 1.5
    speech_min_wordlist_level: float = 3.0
    speech_min_sentence_level: float = 7.0

class GameRuntime:
    def __init__(self, client: OpenAI, scenario: ScenarioDefinition, config: RuntimeConfig):
        self.scenario = scenario
        self.conversation = Conversation()
        self.curator_notes = CuratorNotes()
        self.curator = Curator(
            client=client,
            model=config.curator_model,
            temperature=config.curator_temperature,
            scenario=scenario
        )
        self.primary_ghost = Ghost(
            client=client,
            model=config.ghost_model,
            temperature=config.ghost_temperature,
            scenario=scenario,
            ghost_role="primary"
        )
        self.secondary_ghost = Ghost(
            client=client,
            model=config.ghost_model,
            temperature=config.ghost_temperature,
            scenario=scenario,
            ghost_role="secondary"
        )
        self.game_state = GameState(
            activity_level=config.initial_activity_level,
            scaling_factor=config.activity_grow_factor,
            timer=config.timer_value or 0
        )