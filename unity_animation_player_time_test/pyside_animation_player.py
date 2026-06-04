from typing import Any, Dict, Tuple, Union
from PySide6.QtCore import QTimer, Signal
from .animation_player import AnimationPlayer

from .kwargs import type_kwargs

from .utils import timer

class PysideAnimationPlayer(AnimationPlayer):
    def __init__(self, signal: Signal, file_path: str, stop_time: float = None,
                 **kwargs: Union[str, bool, Tuple, float]):
        """All available kwargs are listed in kwargs.py"""
        
        self.parameters = type_kwargs(**kwargs)

        super().__init__(file_path, stop_time)

        self.signal = signal
        self.mode = 1  # 0: stop, >0: forward_play, <0: backward_play
        self.time_reverse = False
        self.t = 0
        self.delta_t = 1/60
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._pyside_play_frame)

    @timer(name="PysideAnimationPlayer._pyside_play_frame", log_threshold=0.001)
    def _pyside_play_frame(self):
        result, self.playable = self.play_frame(self.t, **self.parameters)
        result ['playable'] = self.playable

        if self.playable:
            self.signal.emit(result)
        else:
            self.signal.emit(self.return_default(path=self.parameters['path'])[0])
            self.timer.stop()

        self.t += self.delta_t * self.mode

    @timer(name="PysideAnimationPlayer.play")
    def play(self, t: float = None, mode: int | float = None):
        if mode is not None:
            self.set_mode(mode)

        if t is not None:
            self.set_time(t)
        elif self.mode >= 0:
            self.set_time(0)
        else:
            self.set_time(self.stop_time)

        self.timer.start(self.delta_t * 1000)

    @timer(name="PysideAnimationPlayer.stop")
    def stop(self):
        self.timer.stop()

    @timer(name="PysideAnimationPlayer.set_time", log_threshold=0.0001)
    def set_time(self, t: float):
        self.t = t

    @timer(name="PysideAnimationPlayer.set_mode", log_threshold=0.0001)
    def set_mode(self, mode: int | float):
        self.mode = mode
        self.parameters['event_time_reverse'] = mode < 0