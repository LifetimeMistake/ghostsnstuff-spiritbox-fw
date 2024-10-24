from datetime import datetime
from typing import Self
from ..utils import clamp

class GameState:
    def __init__(self, activity_level = 1.0, scaling_factor = 0.1, timer = 0.0) -> Self:
        self.initial_activity_level = activity_level
        self.activity_scaling_factor = scaling_factor
        self.initial_timer = timer
        self.reset()
        
    def set_activity_level(self, level):
        self.activity_level = round(clamp(level, 1.0, 10.0), 3)
        
    def reset(self):
        self.set_activity_level(self.initial_activity_level)
        self.timer = self.initial_timer
        if self.initial_timer:
            self.__timer_begin = datetime.now()
        else:
            self.__timer_begin = None
        
    def increment_activity(self):
        self.set_activity_level(self.activity_level + self.activity_scaling_factor)
        
    def get_remaining_time(self) -> float:
        if self.__timer_begin is None:
            return -1
        
        return max(0, self.timer - (datetime.now() - self.__timer_begin).total_seconds())