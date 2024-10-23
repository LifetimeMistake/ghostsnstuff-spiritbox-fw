from pydantic import BaseModel
from ..scenario import ScenarioDefinition

class WriterResponse(BaseModel):
    scenario: ScenarioDefinition
    reasoning: str