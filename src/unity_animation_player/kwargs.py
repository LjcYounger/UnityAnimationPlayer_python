from typing import Tuple, Literal, Union, TypedDict

class PlayKwargsDict(TypedDict, total=False):
    path: str
    time_reverse: bool
    event_time_reverse: bool
    euler_unit: Union[Literal['x', 'y', 'z'], Tuple[Literal['x', 'y', 'z'], ...]]
    rotation_unit: Union[Literal['x', 'y', 'z', 'w'], Tuple[Literal['x', 'y', 'z', 'w'], ...]]
    position_unit: Union[Literal['x', 'y', 'z', 'w'], Tuple[Literal['x', 'y', 'z', 'w'], ...]]
    position_reverse: Union[bool, Tuple[bool, ...]]
    position_ratio: Union[float, Tuple[float, ...]]
    scale_unit: Union[Literal['x', 'y', 'z', 'w'], Tuple[Literal['x', 'y', 'z', 'w'], ...]]
    scale_reverse: Union[bool, Tuple[bool, ...]]
    scale_ratio: Union[float, Tuple[float, ...]]

class PlayKwargs:
    # Default value definitions
    default_path = 'general'
    default_time_reverse = False
    default_event_time_reverse = False
    default_euler_unit = 'z'
    default_rotation_unit = 'w'
    default_position_unit = ('x', 'y')
    default_position_reverse = False
    default_position_ratio = 1.0
    default_scale_unit = ('x', 'y')
    default_scale_reverse = False
    default_scale_ratio = 1.0

    full_euler_unit = ('x', 'y', 'z')
    full_rotation_unit = ('x', 'y', 'z', 'w')
    full_position_unit = ('x', 'y', 'z')
    full_scale_unit = ('x', 'y', 'z')

def type_kwargs(**kwargs) -> PlayKwargsDict:
    """
    Describes the optional keyword arguments for the play method.
    total=False indicates that all fields are optional, which aligns with the characteristics of **kwargs.
    
    euler_unit, rotation_unit, position_unit can accept either a single string or a tuple of strings within their respective ranges.
    position_reverse and position_ratio behavior:
    - If single value, apply to all coordinates
    - If tuple, apply sequentially to corresponding coordinates
    """
    
    typed_kwargs: PlayKwargsDict = {
        'path': str(kwargs.get('path', PlayKwargs.default_path)),
        'time_reverse': bool(kwargs.get('time_reverse', PlayKwargs.default_time_reverse)),
        'event_time_reverse': bool(kwargs.get('event_time_reverse', PlayKwargs.default_event_time_reverse)),
        'euler_unit': kwargs.get('euler_unit', PlayKwargs.default_euler_unit),
        'rotation_unit': kwargs.get('rotation_unit', PlayKwargs.default_rotation_unit),
        'position_unit': kwargs.get('position_unit', PlayKwargs.default_position_unit),
        'position_reverse': kwargs.get('position_reverse', PlayKwargs.default_position_reverse),
        'position_ratio': kwargs.get('position_ratio', PlayKwargs.default_position_ratio),
        'scale_unit': kwargs.get('scale_unit', PlayKwargs.default_scale_unit),
        'scale_reverse': kwargs.get('scale_reverse', PlayKwargs.default_scale_reverse),
        'scale_ratio': kwargs.get('scale_ratio', PlayKwargs.default_scale_ratio)
    }
    return typed_kwargs