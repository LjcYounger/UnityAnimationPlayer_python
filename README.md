# Unity Animation Player for Python

These scripts enable you to play smooth 2D/3D Unity animations in Python.

It is particularly useful when you need to animate window elements, create GUI effects, or preview Unity animations outside the Unity Editor.

## Features

- Parse and play Unity `.anim` files in Python
- Support for Position, Rotation, Scale, and Euler curves
- Full Hermite spline interpolation with weight support
- Animation event system with callback registration
- JIT acceleration with numba for high performance
- PySide6 integration for real-time GUI animation
- Interactive debugging panel with real-time parameter adjustment
- Multiple output formats (Pygame, PySide6, QML)

## Quick Start

Run the example selector:

```bash
python example.py
```

Available examples:
- `interactive_panel` - Interactive animation debugging panel
- `pygame_viewer` - Pygame-based animation viewer
- `pyside_popup_window` - PySide6 popup window animation
- `qml_window` - QML animation window (ball animation, button scaling)

## Basic Usage

```python
from unity_animation_player import AnimationPlayer

# Load animation
player = AnimationPlayer("examples/AnimationClip/T.anim")

# Get animation state at 0.5 seconds
result, valid = player.play_frame(0.5, path="general")

if valid:
    print(f"Position: {result.get('position')}")
    print(f"Scale: {result.get('scale')}")
    print(f"Rotation: {result.get('rotation')}")
```

## Parameter Configuration

Control animation output with flexible parameters:

```python
# Map Unity coordinates to screen coordinates
result, valid = player.play_frame(0.5,
    position_unit=('x', 'y'),
    position_ratio=(19.2, 10.8),   # Scale X and Y independently
    position_reverse=(False, True)  # Reverse Y axis
)
```

## GUI Integration

```python
from PySide6.QtCore import Signal
from unity_animation_player import SignalAnimationPlayer

class MyWindow(QWidget):
    anim_signal = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self.player = SignalAnimationPlayer(
            self.anim_signal, 
            "animation.anim"
        )
        self.anim_signal.connect(self.on_frame)
        self.player.play()
    
    def on_frame(self, data):
        if data.get('playable'):
            pos = data.get('position')
            self.move(*pos)
```

## Animation Events

Register callbacks for Unity animation events:

```python
def on_event(data, float_param):
    print(f"Event: {data}, {float_param}")

player.register_event('eventTriggered', on_event, ('data', 'floatParameter'))
```

## Performance

- SHA256-based JSON caching for fast reloading
- Numba JIT compilation for core interpolation
- PyYAML CLoader for fast YAML parsing

## Requirements

- Python >= 3.8
- numpy
- PyYAML
- PySide6 (for GUI features)
- numba (optional, for JIT acceleration)

## Installation

```bash
pip install numpy pyyaml PySide6
```

For optimal performance:
```bash
pip install numba
```

## Advanced Features

- **Rational Bezier interpolation** - Full Unity curve matching
- **Weight mode support** - Now fully implemented
- **Independent axis control** - Per-axis unit, reverse, and ratio
- **Event time reversal** - Events trigger correctly when playing in reverse
- **Dynamic event addition** - Add custom events at runtime

## Before vs After

The initial version had limitations with weight mode support. The current version fully implements Unity's interpolation system, including weighted Bezier curves and proper handling of infinite slopes.

## License

MIT License

## Contributing

Issues and pull requests are welcome.

## Documentation

Detailed Documentation in https://ljcyounger.github.io/UnityAnimationPlayer_python/