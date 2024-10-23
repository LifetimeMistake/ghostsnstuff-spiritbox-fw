from typing import Self
from openai import OpenAI
from pydantic import BaseModel
from jinja2 import Template
from .models.curator import CuratorNotes, CuratorActionResponse
from .models.state import GameState
from .scenario import ScenarioDefinition
from .conversation import Conversation
from .prompts import CURATOR_PROMPT, CURATOR_USER_PROMPT

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
    def __init__(self, client: OpenAI, model: str, temperature: float, scenario: ScenarioDefinition, prompt: str = CURATOR_PROMPT, user_prompt: str = CURATOR_USER_PROMPT) -> Self:
        prompt_tpl = Template(prompt)
        self.query_tpl = Template(user_prompt)
        rendered_prompt = prompt_tpl.render(
            scneario=scenario
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