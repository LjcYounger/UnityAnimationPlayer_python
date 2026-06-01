from .animation_player import AnimationPlayer
from .pyside_animation_player import PysideAnimationPlayer
from .animation_events import AnimationEvents
from .kwargs import PlayKwargs, PlayKwargsDict, type_kwargs
from .numba_interpolaion import RationalBezierInterpolation
from .config import USE_JIT

if USE_JIT:
    # Compile in advance
    _ = RationalBezierInterpolation(0, 1, 0, 1, 0, 0, 1, 1, 1, 1)
    _(0.5)

__all__ = [
    "AnimationPlayer",
    "PysideAnimationPlayer",
    "AnimationEvents",
    "PlayKwargs",
    "PlayKwargsDict",
    "type_kwargs"
]