from typing import Literal, Optional

GhostRole = Literal["primary", "secondary"]
MessageRole = GhostRole | Literal["user", "curator"]

class Message:
    def __init__(self, role: MessageRole, content: str):
        self.role = role
        self.content = content

class Conversation:
    def __init__(self, history: Optional[list[Message]] = None):
        self.history = history or []

    def __str__(self):
        buffer = []
        user_message_found = False
        for message in reversed(self.history):
            if message.role == "user" and not user_message_found:
                buffer.append(f"(current interaction) >> {message.role}: {message.content}")
                user_message_found = True
            else:
                buffer.append(f"{message.role}: {message.content}")
        return "\n".join(reversed(buffer))
    
    def push(self, message: Message):
        self.history.append(message)

    def clear(self):
        self.history = []