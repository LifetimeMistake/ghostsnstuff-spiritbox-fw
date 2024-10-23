from typing import Literal, Optional

class Message:
    def __init__(self, role: Literal["user"] | Literal["primary"] | Literal["secondary"], content: str):
        self.role = role
        self.content = content

class Conversation:
    def __init__(self, history: Optional[list[Message]] = None):
        self.history = history or []

    def __str__(self):
        buffer = []
        for message in self.history:
            buffer.append(f"{message.role}: {message.content}")

        return "\n".join(buffer)
    
    def push(self, message: Message):
        self.history.append(message)

    def clear(self):
        self.history = []