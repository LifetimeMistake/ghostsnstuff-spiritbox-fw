from openai import OpenAI
from typing import Self, Optional
from .scenario import ScenarioDefinition
from .models.curator import CuratorNotes, CuratorActionResponse
from .models.ghost import GhostResponse
from .models.state import GameState
from .agents import Curator, Ghost
from .conversation import Conversation, Message, MessageRole, GhostRole

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
    speech_min_sentence_level: float = 6.0

class GameRuntime:
    def __init__(self, client: OpenAI, scenario: ScenarioDefinition, config: RuntimeConfig) -> Self:
        self.config = config
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

    def __push_message(self, role: MessageRole, content: list[str | str]):
        message = Message(role, content if isinstance(content, str) else ", ".join(content))
        self.conversation.push(message)

    def __set_ghost_note(self, ghost: GhostRole, note: str | None):
        notes = self.curator_notes

        if ghost == "primary":
            notes.primary_ghost_note = note
        elif ghost == "secondary":
            notes.secondary_ghost_note = note
        else:
            print(f"WARN: Attempted to set curator note for invalid ghost entity type: {ghost}")

    def __execute_curator(self, query, agent_choice) -> CuratorActionResponse:
        state = self.game_state

        response = self.curator.ask(
            state=self.game_state,
            conv=self.conversation,
            notes=self.curator_notes,
            query=query,
            ghost_turn=agent_choice
        )

        primary_note = response.primary_ghost_note
        secondary_note = response.secondary_ghost_note

        # Update ghost notes, also replacing "" with None
        if primary_note is not None:
            self.__set_ghost_note("primary", primary_note or None)

        if secondary_note is not None:
            self.__set_ghost_note("secondary", secondary_note or None)

        # Update activity level
        if response.activity_level is not None:
            delta_activity = state.activity_level - response.activity_level
            activity_shift_str = f"{state.activity_level}->{response.activity_level}"
            if abs(delta_activity) > 1:
                print(f"WARN: Curator attempted to set invalid activity level: {activity_shift_str}")
            else:
                state.activity_level = response.activity_level
                print(f"Curator set activity level to {response.activity_level}")
                self.__push_message("curator", f"(updated activity level: {activity_shift_str})")

        # Update game timer
        if response.timer_value is not None:
            if state.get_remaining_time() == -1:
                print("WARN: Curator attempted to set timer when scenario didn't include one")
            else:
                state.timer += response.timer_value
                timer_shift_str = (
                    f"added {response.timer_value} seconds to the scenario timer" if response.timer_value >= 0
                    else f"removed {abs(response.timer_value)} from the scenario timer"
                )

                print(f"Curator {timer_shift_str}")
                self.__push_message("curator", f"({timer_shift_str})")

        return response

    def __execute_ghost(self, query, agent_choice) -> bool:
        pass

