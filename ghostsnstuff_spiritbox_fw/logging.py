from typing import Self, Literal, Dict, Any
from .events import EventTimeline, Event, EventActor
import logging

LogLevel = Literal["INFO", "WARN", "ERROR"]

class ConsoleLog(Event):
    def __init__(self, actor: EventActor, level: LogLevel, message: str) -> Self:
        super().__init__(actor, "log")
        self.level = level
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "level": self.level,
            "message": self.message
        }

class Logger:
    def __init__(self, timeline: EventTimeline) -> Self:
        self.timeline = timeline

    def __push(self, level: LogLevel, msg: str):
        self.timeline.push(ConsoleLog("System", level, msg))

    def print(self, msg: str):
        logging.info(msg)
        self.__push("INFO", msg)

    def warn(self, msg: str):
        logging.warning(msg)
        self.__push("WARN", msg)
        
    def error(self, msg: str):
        logging.error(msg)
        self.__push("ERROR", msg)