import heapq
from typing import Callable, List
from .utils import timer

class AnimationEvents:
    def __init__(self, raw_events):
        self.events = []
        for raw_event in raw_events:
            self.add_event(raw_event['time'], {k: v for k, v in raw_event.items() if k != 'time'})
        self.events_backup = self.events.copy()
    
    @timer(name="AnimationEvents.add_event", log_threshold=0.0001)
    def add_event(self, delay, *kwargs) -> None:
        heapq.heappush(self.events, (delay, kwargs))

    @timer(name="AnimationEvents.get_events", log_threshold=0.0001)
    def get_events(self, t: float, time_reverse=False) -> List[list]:
        triggered_events = []
        # 根据时间方向决定触发条件
        condition = lambda event_time: event_time >= t if time_reverse else event_time <= t
        
        while self.events and condition(self.events[0][0]):
            event = heapq.heappop(self.events)[1][0]
            triggered_events.append([event['functionName'], {k: v for k, v in event.items() if k != 'functionName'}])
        return triggered_events
    
    @timer(name="AnimationEvents.reset_events")
    def reset_events(self) -> None:
        self.events = self.events_backup.copy()