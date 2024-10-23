from pydantic import BaseModel

class MockUserResponse(BaseModel):
    thoughts: str # The internal thoughts of the user
    content: str # The sentence the mock user wishes to say

    class Config:
        schema_extra = {
            "example": {
                "thoughts": "The ghost hasn't responded in quite a while, so I will make sure it's still present.",
                "content": "Are you still here?",
            }
        }