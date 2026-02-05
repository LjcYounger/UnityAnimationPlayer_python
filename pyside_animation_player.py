from typing import TypedDict, Tuple, Literal
from PySide6.QtCore import QTimer, Signal
from animation_player import AnimationPlayer
from dacite import from_dict
from dataclasses import dataclass, asdict
@dataclass
class PlayKwargs:
    """
    Describes the optional keyword arguments for the play method.
    total=False indicates that all fields are optional, which aligns with the characteristics of **kwargs.
    """
    path: str = 'general'
    timeReverse: bool = False
    Eunit: Literal['x', 'y', 'z'] = 'z'
    Runit: Literal['x', 'y', 'z', 'w'] = 'w'
    Punit: Tuple[Literal['x', 'y', 'z', 'w'], Literal['x', 'y', 'z', 'w']] = ('x', 'y')
    Preverse: Tuple[bool, bool] = (False, False)
    Pratio: Tuple[float, float] = (1.0, 1.0)


class PysideAnimationPlayer(AnimationPlayer):
    def __init__(self, signal: Signal, anim_path: str, stop_time: float = None,
                 **kwargs):
        super().__init__(anim_path, stop_time)
        self.signal = signal
        self.parameters = asdict(from_dict(PlayKwargs, kwargs))
        self.mode = 0  # 0: stop, 1: forward_play, -1: backward_play
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
        self.mode = 1
        self.timer.start(self.delta_t * 1000)

