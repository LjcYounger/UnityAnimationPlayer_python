from typing import Any, Dict, Tuple, Union
from PySide6.QtCore import QTimer, Signal
from animation_player import AnimationPlayer

from kwargs import type_kwargs

class PysideAnimationPlayer(AnimationPlayer):
    def __init__(self, signal: Signal, file_path: str, stop_time: float = None,
                 **kwargs: Union[str, bool, Tuple, float]):
        """All available kwargs are listed in kwargs.py"""
        
        self.parameters = type_kwargs(**kwargs)

        super().__init__(file_path, stop_time)

        self.signal = signal
        self.mode = 1  # 0: stop, 1: forward_play, -1: backward_play
        self.t = 0
        self.delta_t = 1/60
        self.timer = QTimer()
        self.timer.timeout.connect(self._pyside_play_frame)

    def _pyside_play_frame(self):
        result, self.playable = self.play_frame(self.t, **self.parameters)
        if self.playable:
            self.signal.emit(result)
        else:
            self.signal.emit(self.return_default(path=self.parameters['path'])[0])
            self.mode = 0
            self.timer.stop()
        if self.mode > 0:
            self.t += self.delta_t * self.mode
        elif self.mode < 0:
            self.t += self.delta_t * self.mode
    def play(self):
        self.timer.start(self.delta_t * 1000)

    def stop(self):
        self.timer.stop()

    def set_time(self, t: float):
        self.t = t

    def set_mode(self, mode: int | float):
        self.mode = mode

