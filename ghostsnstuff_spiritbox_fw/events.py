from typing import Self, Literal, List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
EventActor = Literal["System", "Primary", "Secondary", "Curator"]

class Event:
    def __init__(self, actor: EventActor, type: str) -> Self:
        self.actor = actor
        self.type = type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "actor": self.actor,
            "type": self.type
        }

class EventTimeline:
    def __init__(self) -> Self:
        self.events = []

    def push(self, event: Event):
        self.events.append(event)

    def list(self) -> List[Event]:
        return self.events
    
    def __repr__(self) -> str:
        return "\n".join(self.list())
