from typing import Self, Optional, Literal
from openai import OpenAI
from pydantic import BaseModel
from jinja2 import Template
from .models.curator import CuratorNotes, CuratorActionResponse
from .models.writer import WriterResponse
from .models.state import GameState
from .models.ghost import GhostResponse
from .scenario import ScenarioDefinition
from .conversation import Conversation
from .prompts import CURATOR_SYSTEM_PROMPT, CURATOR_USER_PROMPT, WRITER_SYSTEM_PROMPT, WRITER_USER_PROMPT, GHOST_SYSTEM_PROMPT, GHOST_USER_PROMPT

class BaseAgent:
    def __init__(self, client: OpenAI, model: str, temperature: float, response_schema: BaseModel, prompt: str) -> Self:
        self.client = client
        self.model = model
        self.temperature = temperature
        self.schema = response_schema
        self.prompt = prompt
        
    def ask(self, question: str) -> BaseModel:
        messages = [
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": question}
        ]
        
        response = self.client.beta.chat.completions.parse(
            messages=messages,
            model=self.model,
            temperature=self.temperature,
            response_format=self.schema
        )
        
        return response.choices[0].message.parsed
    
class Curator:
    def __init__(self, client: OpenAI, model: str, temperature: float, scenario: ScenarioDefinition, prompt: str = CURATOR_SYSTEM_PROMPT, user_prompt: str = CURATOR_USER_PROMPT) -> Self:
        prompt_tpl = Template(prompt)
        self.query_tpl = Template(user_prompt)
        rendered_prompt = prompt_tpl.render(
            scenario=scenario
        )
        self.agent = BaseAgent(
            client=client,
            model=model,
            temperature=temperature,
            response_schema=CuratorActionResponse,
            prompt=rendered_prompt
        )

    def ask(self, state: GameState, conv: Conversation, notes: CuratorNotes, query: str) -> CuratorActionResponse:
        prompt = self.query_tpl.render(
            game_state=state,
            transcript=str(conv),
            curator_notes=notes,
            query=query
        )

        return self.agent.ask(prompt)
    
class Writer:
    def __init__(self, client: OpenAI, model: str, temperature: float, prompt: str = WRITER_SYSTEM_PROMPT, user_prompt: str = WRITER_USER_PROMPT) -> Self:
        self.query_tpl = Template(user_prompt)
        self.agent = BaseAgent(
            client=client,
            model=model,
            temperature=temperature,
            response_schema=WriterResponse,
            prompt=prompt
        )

    def generate(self, prompt: str, scenario_type: str, scenario_example: Optional[ScenarioDefinition] = None) -> WriterResponse:
        prompt = self.query_tpl.render(
            scenario_type=scenario_type,
            scenario_prompt=prompt,
            scenario_example=scenario_example or "N/A"
        )

        return self.agent.ask(prompt)
    
class Ghost:
    def __init__(self, client: OpenAI, model: str, temperature: float, scenario: ScenarioDefinition, ghost_role: Literal["primary"] | Literal["secondary"], prompt: str = GHOST_SYSTEM_PROMPT, user_prompt: str = GHOST_USER_PROMPT) -> Self:
        prompt_tpl = Template(prompt)
        self.query_tpl = Template(user_prompt)
        if ghost_role == "primary":
            self_role = "Primary"
            self_ghost = scenario.primary_ghost
            other_ghost = scenario.secondary_ghost
        else:
            self_role = "Secondary"
            self_ghost = scenario.secondary_ghost
            other_ghost = scenario.primary_ghost

        rendered_prompt = prompt_tpl.render(
            scenario=scenario,
            ghost_role=self_role,
            ghost=self_ghost,
            other_ghost=other_ghost
        )

        self.agent = BaseAgent(
            client=client,
            model=model,
            temperature=temperature,
            response_schema=GhostResponse,
            prompt=rendered_prompt
        )

    def ask(self, state: GameState, conv: Conversation, note: str, query: str) -> GhostResponse:
        prompt = self.query_tpl.render(
            game_state=state,
            transcript=str(conv),
            curator_note=note or "N/A",
            query=query
        )

        return self.agent.ask(prompt)