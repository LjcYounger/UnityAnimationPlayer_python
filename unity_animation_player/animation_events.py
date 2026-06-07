import heapq
from typing import Callable, List

class AnimationEvents:
    def __init__(self, raw_events):
        self.events = []
        self._event_counter = 0  # 用于生成唯一的事件ID，避免heapq比较字典
        for raw_event in raw_events:
            self.add_event(raw_event['time'], {k: v for k, v in raw_event.items() if k != 'time'})
        self.events_backup = self.events.copy()
    
    def add_event(self, delay, *kwargs) -> None:
        self._event_counter += 1
        heapq.heappush(self.events, (delay, self._event_counter, kwargs))

    def get_events(self, t: float, time_reverse=False) -> List[list]:
        triggered_events = []
        # 根据时间方向决定触发条件
        condition = lambda event_time: event_time >= t if time_reverse else event_time <= t
        
        while self.events and condition(self.events[0][0]):
            event = heapq.heappop(self.events)[2][0]  # 索引从1改为2，因为现在元组有3个元素
            triggered_events.append([event['functionName'], {k: v for k, v in event.items() if k != 'functionName'}])
        return triggered_events
    
    def reset_events(self) -> None:
        self.events = self.events_backup.copy()