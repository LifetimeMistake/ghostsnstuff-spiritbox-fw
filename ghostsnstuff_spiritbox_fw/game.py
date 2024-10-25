from random import random
from openai import OpenAI
from typing import Self, Optional, List
from .scenario import ScenarioDefinition
from .models.curator import CuratorNotes, GameResult
from .models.ghost import GhostResponse
from .models.state import GameState
from .agents import Curator, Ghost
from . import logging
from .events import Event, EventTimeline, EventActor
from .conversation import Conversation, Message, MessageRole, GhostRole
from .utils import sanitize_ghost_speech, weighted_ghost_choice

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
    speech_max_wordlist_words: int = 3
    speech_max_sentence_words: int = 5

class CuratorActions:
    new_activity_level: Optional[int] = None
    new_primary_note: Optional[str] = None
    new_secondary_note: Optional[str] = None
    new_timer_value: Optional[float] = None
    game_result: Optional[GameResult] = None
    corrected_user_prompt: Optional[str] = None

class GhostActions:
    glitch: bool = False
    speech: List[str] | str | None = None
    
class RuntimeExecutionResult:
    curator_actions: CuratorActions
    primary_ghost_actions: Optional[GhostActions]
    secondary_ghost_actions: Optional[GhostActions]
    activity_level: float
    game_result: Optional[GameResult]

class GhostCallEvent(Event):
    def __init__(self, actor: EventActor, ghost_call: GhostActions):
        super().__init__(actor, "ghost_call")
        self.used_glitch = ghost_call.glitch
        self.speech = ghost_call.speech

    def to_dict(self):
        return {
            **super().to_dict(),
            "used_glitch": self.used_glitch,
            "speech": ", ".join(self.speech) if isinstance(self.speech, list) else self.speech
        }
    
class CuratorCallEvent(Event):
    def __init__(self, actor: EventActor, curator_call: CuratorActions):
        super().__init__(actor, "curator_call")
        self.data = curator_call
    
    def to_dict(self):
        return {
            **super().to_dict(),
            "new_primary_note": self.data.new_primary_note,
            "new_secondary_note": self.data.new_secondary_note,
            "new_activity_level": self.data.new_activity_level,
            "new_timer_value": self.data.new_timer_value,
            "game_result": self.data.game_result
        }

class GameRuntime:
    def __init__(self, client: OpenAI, scenario: ScenarioDefinition, config: RuntimeConfig, timeline: EventTimeline) -> Self:
        self.config = config
        self.scenario = scenario
        self.events = timeline
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
            logging.warn(f"Attempted to set curator note for invalid ghost entity type: {ghost}")

    def __execute_curator(self, query: str, agent_choice: GhostRole) -> CuratorActions:
        state = self.game_state

        response = self.curator.ask(
            state=state,
            conv=self.conversation,
            notes=self.curator_notes,
            query=query,
            ghost_turn=agent_choice
        )

        actions = CuratorActions()

        primary_note = response.primary_ghost_note
        secondary_note = response.secondary_ghost_note

        # Update ghost notes, also replacing "" with None
        if primary_note is not None:
            self.__set_ghost_note("primary", primary_note or None)
            actions.new_primary_note = primary_note or None

        if secondary_note is not None:
            self.__set_ghost_note("secondary", secondary_note or None)
            actions.new_secondary_note = secondary_note or None

        # Update activity level
        if response.activity_level is not None:
            delta_activity = state.activity_level - response.activity_level
            activity_shift_str = f"{state.activity_level}->{response.activity_level}"
            if abs(delta_activity) > 1:
                logging.warn(f"Curator attempted to set invalid activity level: {activity_shift_str}")
            else:
                state.activity_level = response.activity_level
                actions.new_activity_level = response.activity_level
                logging.print(f"Curator set activity level to {response.activity_level}")
                self.__push_message("curator", f"(updated activity level: {activity_shift_str})")

        # Update game timer
        if response.timer_value is not None:
            if state.get_remaining_time() == -1:
                logging.warn("Curator attempted to set timer when scenario didn't include one")
            else:
                state.timer += response.timer_value
                timer_shift_str = (
                    f"added {response.timer_value} seconds to the scenario timer" if response.timer_value >= 0
                    else f"removed {abs(response.timer_value)} from the scenario timer"
                )
                actions.new_timer_value = state.get_remaining_time()

                logging.print(f"Curator {timer_shift_str}")
                self.__push_message("curator", f"({timer_shift_str})")
                
        # Update user query
        if response.user_prompt_correction is not None:
            logging.print(f"Curator corrected user query to {response.user_prompt_correction}")
            actions.corrected_user_prompt = response.user_prompt_correction

        self.events.push(CuratorCallEvent("Curator", actions))
        return actions

    def __execute_ghost(self, query: str, agent_choice: GhostRole) -> GhostResponse:
        if agent_choice == "primary":
            model = self.primary_ghost
            note = self.curator_notes.primary_ghost_note
        elif agent_choice == "secondary":
            model = self.secondary_ghost
            note = self.curator_notes.secondary_ghost_note
        else:
            logging.warn("Invalid ghost model queued for execution")
            return None
        
        config = self.config
        state = self.game_state
        response = model.ask(
            state=state,
            conv=self.conversation,
            note=note,
            query=query
        )

        actions = GhostActions()

        # Process 
        if response.glitch:
            if state.activity_level < config.glitch_min_level:
                logging.warn("Ghost attempted to glitch EMF, but it wasn't allowed to")
            else:
                self.__glitch()
                actions.glitch = True
                self.__push_message(Message(agent_choice, "(glitched the EMF and audio)"))
        
        # Process vocal response
        if response.content:
            max_words = (
                config.speech_max_wordlist_words if isinstance(response.content, list) 
                else config.speech_max_sentence_words
            )

            sanitized_content = sanitize_ghost_speech(response.content, max_words)
            if isinstance(sanitized_content, str):
                self.__push_message(Message(agent_choice, sanitized_content))
            else:
                self.__push_message(Message(agent_choice, ", ".join(sanitized_content)))

            actions.speech = sanitized_content

        self.events.push(GhostCallEvent(agent_choice.capitalize(), actions))
        return actions
    
    def execute(self, query: str) -> RuntimeExecutionResult:
        state = self.game_state
        self.__push_message("user", query)
        agent_choice = weighted_ghost_choice(state.activity_level)
        execution_result = RuntimeExecutionResult()
        
        curator_run = self.__execute_curator(query, agent_choice)
        if curator_run.corrected_user_prompt:
            # Hacky solution to fix this thing
            for message in reversed(self.conversation.history):
                if message.role != "user":
                    break
                if message.content != query:
                    logging.warn(f"Failed to apply curator correction because the queries were mismatched: expected '{query}' found '{message.content}'")
                    break
                message.content = curator_run.corrected_user_prompt
                query = curator_run.corrected_user_prompt
                break
            
        if curator_run.game_result:
            # End the iteration early
            execution_result.game_result = curator_run.game_result
            return execution_result
        
        execution_result.curator_actions = curator_run
        if agent_choice == "primary":
            execution_result.primary_ghost_actions = self.__execute_ghost(query, agent_choice)
        elif agent_choice == "secondary":
            execution_result.secondary_ghost_actions = self.__execute_ghost(query, agent_choice)
        elif agent_choice == "both":
            order = random.choice([True, False])
            if order:
                execution_result.primary_ghost_actions = self.__execute_ghost(query, "primary")
                execution_result.secondary_ghost_actions = self.__execute_ghost(query, "secondary")
            else:
                execution_result.primary_ghost_actions = self.__execute_ghost(query, "secondary")
                execution_result.secondary_ghost_actions = self.__execute_ghost(query, "primary")
        
        state.increment_activity()
        logging.info(f"Activity level is now {state.activity_level}")
        execution_result.activity_level = state.activity_level
        return execution_result