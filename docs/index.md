# Unity Animation Player Documentation

## Overview

Unity Animation Player is a Python library for parsing and playing animation files (.anim) exported from the Unity engine. It implements core features of Unity's animation system, including Hermite curve interpolation, rational Bezier curves, SLERP quaternion interpolation, and animation event triggering.

---

## Quick Start

### Basic Usage

```python
from unity_animation_player import AnimationPlayer

# Load animation file
player = AnimationPlayer("examples/AnimationClip/T.anim")

# Get animation duration
print(f"Animation duration: {player.stop_time} seconds")

# Get animation state at specific time
result, valid = player.play_frame(0.5, path="general")
if valid:
    print(f"Position: {result.get('position')}")
    print(f"Scale: {result.get('scale')}")
    print(f"Rotation: {result.get('rotation')}")
```

### Sampling Animation Curves

```python
# Sample entire animation at 0.01 second intervals
samples = player.sample_range(sample_rate=0.01)

for time, data in samples.items():
    position = data.get('position')
    # Process sampled data...
```

---

## Installation

### Dependencies

- Python >= 3.8
- numpy
- PyYAML (with CLoader)
- qtpy (optional, for Qt signal support)
- PySide6 (optional, for GUI features)
- numba (optional, for JIT acceleration)

### Installation Steps

```bash
pip install numpy pyyaml qtpy PySide6 numba
```

### JIT Configuration

Edit `unity_animation_player/config.py`:

```python
USE_JIT = True   # Enable numba JIT acceleration
FPS = 60         # Default frame rate for SignalAnimationPlayer
```

---

## Core Classes

### AnimationPlayer

Main animation playback class responsible for parsing animation files and providing time-based sampling.

**Constructor**

```python
AnimationPlayer(path: str, stop_time: Optional[float] = None)
```

| Parameter | Type  | Description                            |
| --------- | ----- | -------------------------------------- |
| path      | str   | Path to .anim file                     |
| stop_time | float | Optional, overrides animation end time |

**Properties**

| Property  | Type            | Description           |
| --------- | --------------- | --------------------- |
| anim      | dict            | Parsed animation data |
| stop_time | float           | Animation end time    |
| events    | AnimationEvents | Event manager         |

**Main Methods**

| Method                                                  | Description                           |
| ------------------------------------------------------- | ------------------------------------- |
| `play_frame(nowtime, **kwargs)`                       | Get animation state at specified time |
| `sample_range(sample_rate, t_start, t_end, **kwargs)` | Batch sample animation data           |
| `register_event(function_name, callback, args)`       | Register animation event callback     |
| `add_event(delay, **kwargs)`                          | Dynamically add event                 |
| `return_default(**kwargs)`                            | Return default values when animation ends |

**play_frame Return Value**

```python
# Return format
(result: dict, valid: bool)

# Possible keys in result
{
    'position': (x, y) or single float,   # Based on position_unit
    'scale': (x, y, z) or single float,   # Based on scale_unit
    'rotation': (x, y, z, w) or single float,  # Based on rotation_unit
    'euler': (x, y, z) or single float,   # Based on euler_unit
    'float': float,                       # Float curve value
    'events': list,                       # Triggered events list
    'playable': bool                      # Whether animation is still playing
}
```

### SignalAnimationPlayer

Inherits from AnimationPlayer, integrates Qt timer for GUI applications.

**Constructor**

```python
SignalAnimationPlayer(signal: Signal, file_path: str, stop_time: float = None, **kwargs)
```

| Parameter | Type    | Description                          |
| --------- | ------- | ------------------------------------ |
| signal    | Signal  | Qt signal to emit animation frames   |
| file_path | str     | Path to .anim file                   |
| stop_time | float   | Optional, overrides animation end time |
| **kwargs  | dict    | Playback parameters (see PlayKwargsDict) |

**Properties**

| Property  | Type    | Description                    |
| --------- | ------- | ------------------------------ |
| mode      | int/float | Playback speed/direction (0=stop, >0=forward, <0=backward) |
| t         | float   | Current animation time         |
| timer     | QTimer  | Qt timer for frame updates     |

**Main Methods**

| Method                           | Description                                     |
| -------------------------------- | ----------------------------------------------- |
| `play(t=None, mode=None)`        | Start playback, default mode=1 forward         |
| `stop()`                         | Stop playback                                   |
| `set_mode(mode)`                 | Set playback speed/direction                    |
| `set_time(t)`                    | Jump to specified time                          |

### AnimationEvents

Event management class for handling animation events.

**Constructor**

```python
AnimationEvents(raw_events: list)
```

**Methods**

| Method                                      | Description                    |
| ------------------------------------------- | ------------------------------ |
| `add_event(delay, *kwargs)`                | Add a new event                |
| `get_events(t, time_reverse)`              | Get events triggered up to time t |
| `reset_events()`                           | Reset event queue to initial state |

---

## Parameter Configuration

### PlayKwargsDict Type

Pass parameters via `**kwargs` to control animation sampling behavior. Use `type_kwargs()` to normalize input.

```python
from unity_animation_player import type_kwargs

kwargs = type_kwargs(
    path="general",
    time_reverse=False,
    position_unit=('x', 'y'),
    position_ratio=1.0,
    position_reverse=False
)

result, valid = player.play_frame(0.5, **kwargs)
```

### Parameter Reference

| Parameter          | Type                              | Default         | Description                                     |
| ------------------ | --------------------------------- | --------------- | ----------------------------------------------- |
| path               | str                               | 'general'       | Animation path (path field in AnimationClip)    |
| time_reverse       | bool                              | False           | Whether to play time in reverse                 |
| event_time_reverse | bool                              | False           | Whether event triggering follows time direction |
| euler_unit         | str or tuple of 'x','y','z'       | 'z'             | Euler angle axis selection                      |
| rotation_unit      | str or tuple of 'x','y','z','w'   | 'w'             | Rotation axis selection (quaternion)            |
| position_unit      | str or tuple of 'x','y','z'       | ('x', 'y')      | Position axis selection                         |
| position_reverse   | bool or tuple of bool             | False           | Whether to negate position values               |
| position_ratio     | float or tuple of float           | 1.0             | Position value scale factor                     |
| scale_unit         | str or tuple of 'x','y','z'       | ('x', 'y', 'z') | Scale axis selection                            |
| scale_reverse      | bool or tuple of bool             | False           | Whether to negate scale values                  |
| scale_ratio        | float or tuple of float           | 1.0             | Scale value scale factor                        |

### Compound Parameter Explanation

- **Single Value Mode**: Apply same setting to all axes

  ```python
  position_reverse = True      # Negate X, Y, Z all
  position_ratio = 2.0         # Scale X, Y, Z all by 2x
  ```

- **Tuple Mode**: Independent settings per axis

  ```python
  position_unit = ('x', 'y')          # Output only X and Y axes
  position_reverse = (False, True)    # X unchanged, Y negated
  position_ratio = (1.0, 2.0)         # X unchanged, Y scaled by 2x
  ```

### type_kwargs Function

```python
type_kwargs(**kwargs) -> PlayKwargsDict
```

Normalizes keyword arguments with default values. Converts string units to tuple when appropriate and ensures proper typing.

---

## Animation Events

Unity animations support triggering events at specific times. This library fully supports this feature.

### Event Structure

Events in animation files are automatically parsed:

```yaml
m_Events:
  - time: 0.41666666
    functionName: eventTriggered
    data: EVENT_TRIGGERED
    floatParameter: 2.8
    intParameter: 6
    messageOptions: 0
```

### Registering Event Callbacks

```python
def on_event_triggered(data, float_param, int_param):
    print(f"Event triggered: {data}, {float_param}, {int_param}")

player.register_event(
    'eventTriggered', 
    on_event_triggered, 
    ('data', 'floatParameter', 'intParameter')
)

# Events are automatically triggered during playback
result, valid = player.play_frame(0.42)
# result['events'] contains triggered event information
```

### Dynamically Adding Events

```python
player.add_event(1.0, {
    'functionName': 'customEvent',
    'data': 'Hello',
    'floatParameter': 3.14
})
```

---

## Advanced Usage

### Custom Coordinate Transformation

Use `position_ratio` and `position_reverse` parameters for flexible coordinate mapping:

```python
# Map Unity coordinates to screen coordinates
# Unity: X range [0, 100], Y range [0, 100]
# Screen: X range [0, 1920], Y range [0, 1080], Y axis reversed

result, valid = player.play_frame(0.5, 
    position_ratio=(19.2, 10.8),  # Scale factors
    position_reverse=(False, True) # Y axis reversed
)
```

### Combining Multiple Transforms

```python
# Get both position and scale with independent configurations
result, valid = player.play_frame(0.5,
    position_unit=('x', 'y'),
    position_ratio=(2.0, 2.0),
    scale_unit=('x', 'y'),
    scale_ratio=1.5
)

if valid:
    pos_x, pos_y = result['position']
    scale_x, scale_y = result['scale']
```

### Dynamically Switching Animation Paths

```python
# Get all available paths in animation
paths = list(player.anim.keys())

# Iterate through all paths
for path in paths:
    result, valid = player.play_frame(0.5, path=path)
    if valid and 'position' in result:
        print(f"{path}: {result['position']}")
```

### Real-time Animation Control

```python
import time
from unity_animation_player import AnimationPlayer

player = AnimationPlayer("animation.anim")
start_time = time.time()
speed = 1.0

while True:
    elapsed = (time.time() - start_time) * speed
    if elapsed > player.stop_time:
        elapsed = elapsed % player.stop_time  # Loop playback
  
    result, valid = player.play_frame(elapsed)
    if valid and 'position' in result:
        # Update object position
        update_object_position(result['position'])
  
    time.sleep(1/60)  # 60 FPS
```

---

## Interpolation System

### Supported Curve Types

| Type           | Description                         | Interpolation Method          |
| -------------- | ----------------------------------- | ----------------------------- |
| PositionCurves | Position curves (X, Y, Z)           | Rational Bezier / Hermite     |
| RotationCurves | Rotation curves (quaternion)        | Spherical Linear (SLERP)      |
| EulerCurves    | Euler angle curves                  | Euler SLERP / Axis-angle      |
| ScaleCurves    | Scale curves (X, Y, Z)              | Rational Bezier / Hermite     |
| FloatCurves    | Float curves                        | Rational Bezier / Hermite     |

### Interpolation Classes

#### RationalBezierInterpolation

Factory function for rational Bezier curve interpolation.

```python
RationalBezierInterpolation(x0, x1, y0, y1, k0, k1, w0=1.0, w1=1.0, w2=1.0, w3=1.0)
```

| Parameter | Description                    |
| --------- | ------------------------------ |
| x0, x1    | Start and end time values      |
| y0, y1    | Start and end values           |
| k0, k1    | Start and end slopes           |
| w0-w3     | Weight parameters (default 1.0) |

#### SphericalLinearInterpolation

Factory function for quaternion SLERP interpolation.

```python
SphericalLinearInterpolation(x0, y0, z0, w0, x1, y1, z1, w1, t0=0.0, t1=1.0, force_axis_angle=False)
```

| Parameter      | Description                                    |
| -------------- | ---------------------------------------------- |
| x0,y0,z0,w0    | Start quaternion components                    |
| x1,y1,z1,w1    | End quaternion components                      |
| t0, t1         | Time range for automatic normalization         |
| force_axis_angle | Force axis-angle mode for 360° rotations    |

#### EulerSphericalLinearInterpolation

Factory function for Euler angle SLERP interpolation.

```python
EulerSphericalLinearInterpolation(euler_x0, euler_y0, euler_z0, euler_x1, euler_y1, euler_z1, t0=0.0, t1=1.0, axis=None)
```

| Parameter | Description                                    |
| --------- | ---------------------------------------------- |
| euler_*0  | Start Euler angles (degrees)                   |
| euler_*1  | End Euler angles (degrees)                     |
| t0, t1    | Time range for automatic normalization         |
| axis      | Optional axis for 360° rotation ('x','y','z') |

---

## Performance Optimization

### YAML Caching

Parsed animation data is cached to a temporary directory with SHA256 checksum validation.

Cache location:

- Windows: `%TEMP%/unity_animation_player_python/`
- Linux/Mac: `/tmp/unity_animation_player_python/`

### JIT Compilation with Numba

Core interpolation algorithms use numba JIT compilation:

```python
# config.py
USE_JIT = True   # Enable JIT (requires numba)
```

When enabled, the following are JIT-compiled:
- `binary_search_segment_index` - Fast time segment lookup
- `_RationalBezierInterpolator` - Rational Bezier evaluation
- `_SphericalLinearInterpolator` - SLERP quaternion evaluation
- `_AxisAngleInterpolator` - Axis-angle rotation evaluation

### PyYAML CLoader

Use LibYAML's C accelerator for faster YAML parsing:

```python
data = yaml.load(content, Loader=yaml.CLoader)
```

---

## GUI Integration

### SignalAnimationPlayer with Qt

```python
from PySide6.QtCore import Signal, QApplication
from unity_animation_player import SignalAnimationPlayer

class MyWidget(QWidget):
    anim_signal = Signal(dict)
  
    def __init__(self):
        super().__init__()
        self.player = SignalAnimationPlayer(
            self.anim_signal, 
            "animation.anim",
            position_ratio=(2.0, 2.0)
        )
        self.anim_signal.connect(self.on_animation_frame)
      
    def on_animation_frame(self, data):
        if data.get('playable'):
            position = data.get('position')
            # Update UI element position
            if position:
                self.move(int(position[0]), int(position[1]))
  
    def start_animation(self):
        self.player.play()  # mode=1 forward from t=0
```

### Custom PopupWindow Base Class

```python
from unity_animation_player import PopupWindow  # Note: Custom class in examples

class MyPopup(PopupWindow):
    def __init__(self):
        super().__init__(darkScreen=True)
        self.play_anim(
            anim="popup.anim",
            path="Center/Popup",
            position_ratio=(1, 0.5)
        )
```

---

## Examples

Run `example.py` to view all examples:

```bash
python example.py
```

Available examples:

| Example Name            | Description                                                               |
| ----------------------- | ------------------------------------------------------------------------- |
| `interactive_panel`     | Interactive animation debugging panel with real-time parameter adjustment |
| `pygame_viewer`         | Pygame-based animation viewer with keyboard controls                      |
| `pyside_popup_window`   | PySide6 popup window animation example                                    |
| `qml_window`            | QML animation window example (ball animation, button scaling)             |

---

## API Reference

### AnimationPlayer

**Methods**

#### play_frame

```python
play_frame(nowtime: float, **kwargs) -> Tuple[dict, bool]
```

Get animation state at specified time.

**Parameters**
- `nowtime`: Time point (seconds)
- `**kwargs`: Playback parameters (see PlayKwargsDict)

**Returns**
- `dict`: Animation state data with keys: position, scale, rotation, euler, float, events
- `bool`: Whether time point is valid

#### sample_range

```python
sample_range(sample_rate: float = 0.01, t_start: float = None, t_end: float = None, **kwargs) -> dict
```

Batch sample animation data.

**Returns**
- `dict`: Dictionary of `{time: animation_data}`

#### register_event

```python
register_event(function_name: str, function: Callable, args: tuple = ())
```

Register event callback function.

**Parameters**
- `function_name`: Event name (matches functionName in animation file)
- `function`: Callback function
- `args`: Tuple of event parameter names to pass to callback

#### add_event

```python
add_event(delay: float, *kwargs)
```

Dynamically add an event.

#### return_default

```python
return_default(default_value: float = 0.0, default_scale: float = 1.0, **kwargs) -> Tuple[dict, bool]
```

Return default values when animation is outside valid time range.

### SignalAnimationPlayer

**Methods**

#### play

```python
play(t: float = None, mode: Union[int, float] = None)
```

Start playback.

**Parameters**
- `t`: Start time (if None, starts at 0 for mode>=0 or stop_time for mode<0)
- `mode`: Playback speed/direction (1=forward, -1=reverse, 0=stop)

#### stop

```python
stop()
```

Stop playback.

#### set_mode

```python
set_mode(mode: Union[int, float])
```

Set playback speed and direction.

#### set_time

```python
set_time(t: float)
```

Jump to specified time.

### Utility Functions

#### type_kwargs

```python
type_kwargs(**kwargs) -> PlayKwargsDict
```

Normalize keyword arguments with default values. Converts string units to tuple format when appropriate.

---

## File Format Support

### Unity YAML Format

The library parses Unity's YAML-based .anim files with support for:

- `AnimationClip` root object
- `m_RotationCurves` - Quaternion rotation curves (SLERP interpolation)
- `m_EulerCurves` - Euler angle curves
- `m_PositionCurves` - Position curves
- `m_ScaleCurves` - Scale curves
- `m_FloatCurves` - Float curves
- `m_Events` - Animation events

### YAML Parsing Features

- Removes `%TAG` directives
- Converts `--- !u!XX &YYY` to `--- &YYY` for cleaner parsing
- Prevents parsing "y" as boolean (treats as string)

---

## License

MIT License