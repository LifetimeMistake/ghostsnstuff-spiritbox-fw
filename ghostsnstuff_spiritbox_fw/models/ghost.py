from typing import Self, Optional, Union
from pydantic import BaseModel

class GhostResponse(BaseModel):
    reasoning: str
    content: Union[list[str], str] = None # The set of words or a sentence the ghost wishes to say.
    glitch: bool # Whether to glitch the EMF/audio

    class Config:
        schema_extra = {
            "example": {
                "reasoning": "The game is still at the initial stage and I can only respond with a few words at a time. My word choice ties into my ominous and cryptic personality.",
                "content": ["HELP", "COLD"],
                "glitch": False,
            }
        }