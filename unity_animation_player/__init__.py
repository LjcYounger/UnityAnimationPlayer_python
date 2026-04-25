from .animation_player import AnimationPlayer
from .pyside_animation_player import PysideAnimationPlayer
from .numba_hermite import CubicHermiteSpline

# Compile in advance
_ = CubicHermiteSpline(0, 1, 0, 1, 0, 0)
_(0.5)

__all__ = [
    "AnimationPlayer",
    "PysideAnimationPlayer"
]