from .animation_player import AnimationPlayer
from .signal_animation_player import SignalAnimationPlayer
from .animation_events import AnimationEvents
from .kwargs import PlayKwargsDict, type_kwargs
from .numba_optimized.rational_bezier_interpolator import RationalBezierInterpolation
from .numba_optimized.spherical_linear_interpolator import SphericalLinearInterpolation, EulerSphericalLinearInterpolation
from . import config

if config.USE_JIT:
    # Compile in advance
    RationalBezierInterpolation(0, 1, 0, 1, 0, 0, 1, 1, 1, 1)(0.5)
    SphericalLinearInterpolation(0, 1, 0, 1, 0, 0, 1, 1, 0, 1)(0.5)
    EulerSphericalLinearInterpolation(0, 1, 0, 1, 0, 0, 0, 1)(0.5)


__all__ = [
    "AnimationPlayer",
    "SignalAnimationPlayer",
    "AnimationEvents",
    "PlayKwargsDict",
    "type_kwargs",
    "config"
]