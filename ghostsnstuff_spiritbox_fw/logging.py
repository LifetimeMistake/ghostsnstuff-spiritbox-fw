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
        if not self.timeline:
            return
        
        self.timeline.push(ConsoleLog("System", level, msg))

    def print(self, msg: str):
        logging.print(msg)
        self.__push("INFO", msg)

    def warn(self, msg: str):
        logging.warning(msg)
        self.__push("WARN", msg)
        
    def error(self, msg: str):
        logging.error(msg)
        self.__push("ERROR", msg)

_logger = Logger(None)

def set_timeline(timeline: EventTimeline):
    _logger.timeline = timeline

def print(msg: str):
    _logger.print(msg)

def warn(msg: str):
    _logger.warn(msg)

def error(msg: str):
    _logger.error(msg)