from typing import Tuple, Literal, Union, TypedDict
from dataclasses import dataclass, asdict
from dacite import from_dict

class PlayKwargsDict(TypedDict, total=False):
    path: str
    timeReverse: bool
    Eunit: Union[Literal['x', 'y', 'z'], Tuple[Literal['x', 'y', 'z'], ...]]
    Runit: Union[Literal['x', 'y', 'z', 'w'], Tuple[Literal['x', 'y', 'z', 'w'], ...]]
    Punit: Union[Literal['x', 'y', 'z', 'w'], Tuple[Literal['x', 'y', 'z', 'w'], ...]]
    Preverse: Union[bool, Tuple[bool, ...]]
    Pratio: Union[float, Tuple[float, ...]]


@dataclass
class PlayKwargs:
    """
    Describes the optional keyword arguments for the play method.
    total=False indicates that all fields are optional, which aligns with the characteristics of **kwargs.
    
    Eunit, Runit, Punit can accept either a single string or a tuple of strings within their respective ranges.
    Preverse and Pratio behavior:
    - If single value, apply to all coordinates
    - If tuple, apply sequentially to corresponding coordinates
    """
    path: str = 'general'
    timeReverse: bool = False
    Eunit: Union[Literal['x', 'y', 'z'], Tuple[Literal['x', 'y', 'z'], ...]] = 'z'
    Runit: Union[Literal['x', 'y', 'z', 'w'], Tuple[Literal['x', 'y', 'z', 'w'], ...]] = 'w'
    Punit: Union[Literal['x', 'y', 'z', 'w'], Tuple[Literal['x', 'y', 'z', 'w'], ...]] = ('x', 'y')
    Preverse: Union[bool, Tuple[bool, ...]] = False
    Pratio: Union[float, Tuple[float, ...]] = 1.0


def type_kwargs(**kwargs) -> PlayKwargsDict:

    default_kwargs = PlayKwargs()
    merged_kwargs = {**asdict(default_kwargs), **kwargs}
    return asdict(from_dict(PlayKwargs, merged_kwargs))