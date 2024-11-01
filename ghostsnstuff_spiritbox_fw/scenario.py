from typing import List, Optional, Literal
from pydantic import BaseModel, TypeAdapter

class RitualDefinition(BaseModel):
    name: str
    description: str
    phrase: str

class Memory(BaseModel):
    memory: str
    hint: str
    solution: str

class GhostDefinition(BaseModel):
    name: str
    personality: str
    goals: str
    backstory: str
    hints: List[str]
    ritual: Optional[RitualDefinition] = None  # This applies to ghosts with rituals
    key_memories: Optional[List[Memory]] = None  # This applies to ghosts with locked key memories
    tts_voice_model: str


class FinalGoalDefinition(BaseModel):
    description: str # Description that includes a textual explanation of the goal
    ritual: Optional[RitualDefinition] = None  # The ritual that needs to be performed in order to win, if any

class ScenarioDefinition(BaseModel):
    scenario_type: str
    scenario_description: str
    primary_ghost: GhostDefinition
    secondary_ghost: GhostDefinition
    shared_lore: str
    final_goal: FinalGoalDefinition

def load_scenario(file: str) -> ScenarioDefinition:
    with open(file, "r") as f:
        return TypeAdapter(ScenarioDefinition).validate_json(f.read())