from typing import Self, Optional, Union
from pydantic import BaseModel

class CuratorNotes:
    def __init__(self) -> Self:
        self.primary_ghost_note = None
        self.secondary_ghost_note = None

# End Condition Struct
class EndCondition(BaseModel):
    game_result: str  # "win" or "fail"
    reasoning: str  # Explanation for ending the game


# Regular Response Struct
class CuratorResponse(BaseModel):
    primary_ghost_note: Optional[str] = None  # Instructions for primary ghost (can be empty to reset)
    secondary_ghost_note: Optional[str] = None  # Instructions for secondary ghost (can be empty to reset)
    activity_level: Optional[float] = None  # Current activity level (1-10, or None if unchanged)
    timer_value: Optional[float] = None  # Remaining timer value (or None if unchanged)
    user_prompt_correction: Optional[str] = None  # Corrected user input (or None if no correction needed)
    reasoning: str  # Reason for the updates made by the curator

    class Config:
        schema_extra = {
            "example": {
                "primary_ghost_note": "The users seem suspicious of you. Be more convincing.",
                "secondary_ghost_note": "Try to encourage the users to listen to the primary ghost.",
                "activity_level": None,
                "timer_value": None,
                "user_prompt_correction": None,
                "reasoning": "I updated the ghost notes because I felt the ghosts were going off on a tangent."
            }
        }

CuratorActionResponse = Union[CuratorResponse, EndCondition]