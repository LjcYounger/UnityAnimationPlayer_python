from typing import Tuple, Literal, Union, TypedDict
from dataclasses import dataclass, asdict
from dacite import from_dict

class PlayKwargsDict(TypedDict, total=False):
    path: str
    time_reverse: bool
    euler_unit: Union[Literal['x', 'y', 'z'], Tuple[Literal['x', 'y', 'z'], ...]]
    rotation_unit: Union[Literal['x', 'y', 'z', 'w'], Tuple[Literal['x', 'y', 'z', 'w'], ...]]
    position_unit: Union[Literal['x', 'y', 'z', 'w'], Tuple[Literal['x', 'y', 'z', 'w'], ...]]
    position_reverse: Union[bool, Tuple[bool, ...]]
    position_ratio: Union[float, Tuple[float, ...]]
    scale_unit: Union[Literal['x', 'y', 'z', 'w'], Tuple[Literal['x', 'y', 'z', 'w'], ...]]
    scale_reverse: Union[bool, Tuple[bool, ...]]
    scale_ratio: Union[float, Tuple[float, ...]]


@dataclass
class PlayKwargs:
    """
    Describes the optional keyword arguments for the play method.
    total=False indicates that all fields are optional, which aligns with the characteristics of **kwargs.
    
    euler_unit, rotation_unit, position_unit can accept either a single string or a tuple of strings within their respective ranges.
    position_reverse and position_ratio behavior:
    - If single value, apply to all coordinates
    - If tuple, apply sequentially to corresponding coordinates
    """
    path: str = 'general'
    time_reverse: bool = False
    euler_unit: Union[Literal['x', 'y', 'z'], Tuple[Literal['x', 'y', 'z'], ...]] = 'z'
    rotation_unit: Union[Literal['x', 'y', 'z', 'w'], Tuple[Literal['x', 'y', 'z', 'w'], ...]] = 'w'
    position_unit: Union[Literal['x', 'y', 'z', 'w'], Tuple[Literal['x', 'y', 'z', 'w'], ...]] = ('x', 'y')
    position_reverse: Union[bool, Tuple[bool, ...]] = False
    position_ratio: Union[float, Tuple[float, ...]] = 1.0
    scale_unit: Union[Literal['x', 'y', 'z', 'w'], Tuple[Literal['x', 'y', 'z', 'w'], ...]] = ('x', 'y', 'z')
    scale_reverse: Union[bool, Tuple[bool, ...]] = False
    scale_ratio: Union[float, Tuple[float, ...]] = 1.0


def type_kwargs(**kwargs) -> PlayKwargsDict:

    default_kwargs = PlayKwargs()
    merged_kwargs = {**asdict(default_kwargs), **kwargs}
    return asdict(from_dict(PlayKwargs, merged_kwargs))