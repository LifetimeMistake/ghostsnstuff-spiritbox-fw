from typing import Self, Optional, Literal
from pydantic import BaseModel

class CuratorNotes:
    def __init__(self) -> Self:
        self.primary_ghost_note = None
        self.secondary_ghost_note = None

GameResult = Literal["win", "lose"]

class CuratorReasoning(BaseModel):
    ghost_performance_reasoning: str
    game_progress_remarks: str

    class Config:
        schema_extra = {
            "example": {
                "ghost_performance_reasoning": "The primary ghost is behaving correctly according to its guidelines. he secondary ghost is yet to speak, but the activity level is still low, therefore its lack of activity is expected. I will not intervene for now. ",
                "game_progress_reasoning": "The users have discovered fragments of the banishment spell, but have yet to put it together and say it out loud. The game should continue."
            }
        }


class CuratorActionResponse(BaseModel):
    state_reasoning: CuratorReasoning
    action_reasoning: str  # Reason for the updates made by the curator
    primary_ghost_note: Optional[str] = None  # Instructions for primary ghost (can be empty to reset)
    secondary_ghost_note: Optional[str] = None  # Instructions for secondary ghost (can be empty to reset)
    activity_level: Optional[float] = None  # Current activity level (1-10, or None if unchanged)
    timer_value: Optional[float] = None  # Remaining timer value (or None if unchanged)
    user_prompt_correction: Optional[str] = None  # Corrected user input (or None if no correction needed)
    game_result: Optional[GameResult] = None

    class Config:
        schema_extra = {
            "example": {
                "state_reasoning": {
                    "ghost_performance_reasoning": "The primary ghost is behaving correctly according to its guidelines. he secondary ghost is yet to speak, but the activity level is still low, therefore its lack of activity is expected. I will not intervene for now. ",
                    "game_progress_reasoning": "The users have discovered fragments of the banishment spell, but have yet to put it together and say it out loud. The game should continue."
                },
                "action_reasoning": "I updated the ghost notes because I felt the ghosts were going off on a tangent.",
                "primary_ghost_note": "The users seem suspicious of you. Be more convincing.",
                "secondary_ghost_note": "Try to encourage the users to listen to the primary ghost.",
                "activity_level": None,
                "timer_value": None,
                "user_prompt_correction": None,
                "game_result": None,
            }
        }