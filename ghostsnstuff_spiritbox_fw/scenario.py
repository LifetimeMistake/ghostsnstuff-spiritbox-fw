from typing import List, Optional
from pydantic import BaseModel


class RitualDefinition(BaseModel):
    name: str
    description: str
    phrase: str

class GhostDefinition(BaseModel):
    name: str
    personality: str
    goals: str
    backstory: str
    hints: List[str]
    ritual: Optional[RitualDefinition] = None  # This applies to ghosts with rituals
    key_memories: Optional[List[str]] = None  # This applies to ghosts with locked key memories


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
