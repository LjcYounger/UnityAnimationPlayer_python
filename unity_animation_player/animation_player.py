from functools import lru_cache
from typing import Callable, Dict, Any, Literal, Tuple, Union, Optional
from dataclasses import asdict

import numpy as np

from .parse_yaml import parse_anim
from .cache_yaml import load_yaml

from .kwargs import type_kwargs
from .animation_events import AnimationEvents
from .numba_optimized.binary_search import binary_search_segment_index
@lru_cache(maxsize=64)
def load_anim(path: str) -> Tuple[Dict[str, Any], float]:
    anim_json = load_yaml(path)
    stop_time, anim, events = parse_anim(anim_json)
    return stop_time, anim, events


class AnimationPlayer:
    def __init__(self, path: str, stop_time: Optional[float] = None):
        self.stop_time, self.anim, raw_events = load_anim(path)

        self.events = AnimationEvents(raw_events)

        self.registered_events = {}

        if stop_time is not None:
            self.stop_time = stop_time

    def play_frame(self,
                   nowtime: float,
                   **kwargs: Union[str, bool, Tuple, float]) -> Tuple[Dict[str, Any], bool]:
        
        typed_kwargs = type_kwargs(**kwargs)

        nowtime1 = nowtime
        if typed_kwargs['time_reverse']:
            nowtime = self.stop_time - nowtime
        if nowtime1 <= self.stop_time and nowtime1 >= 0:
            dic: Dict[str, Any] = {}
            ani = self.anim[typed_kwargs['path']]
            if 'Euler' in ani:
                e, time_nodes = ani.get('Euler')

                euler_unit = typed_kwargs['euler_unit']
                if isinstance(euler_unit, tuple):
                    euler = tuple(self._get_seg_result(e[unit], nowtime, time_nodes) for unit in euler_unit)
                else:
                    euler = self._get_seg_result(e[euler_unit], nowtime, time_nodes)
                dic['euler'] = euler

            if 'Rotation' in ani:
                r, time_nodes = ani.get('Rotation')

                rotation_unit = typed_kwargs['rotation_unit']
                if isinstance(rotation_unit, tuple):
                    rotation = tuple(self._get_seg_result(r[unit], nowtime, time_nodes) for unit in rotation_unit)
                else:
                    rotation = self._get_seg_result(r[rotation_unit], nowtime, time_nodes)
                dic['rotation'] = rotation

            if 'Position' in ani:
                p, time_nodes = ani.get('Position')

                position_unit = typed_kwargs['position_unit']
                position_reverse = typed_kwargs['position_reverse']
                position_ratio = typed_kwargs['position_ratio']
                
                if isinstance(position_unit, tuple):

                    position_values = []
                    for i, unit in enumerate(position_unit):

                        reverse_val = position_reverse[i] if isinstance(position_reverse, tuple) else position_reverse
                        ratio_val = position_ratio[i] if isinstance(position_ratio, tuple) else position_ratio
                        pos_val = self._get_seg_result(p[unit], nowtime, time_nodes) * ratio_val
                        pos_val = -pos_val if reverse_val else pos_val
                        position_values.append(pos_val)
                    dic['position'] = tuple(position_values)
                else:

                    reverse_val = position_reverse if isinstance(position_reverse, bool) else position_reverse[0]
                    ratio_val = position_ratio if isinstance(position_ratio, (int, float)) else position_ratio[0]
                    pos_val = self._get_seg_result(p[position_unit], nowtime, time_nodes) * ratio_val
                    pos_val = -pos_val if reverse_val else pos_val
                    dic['position'] = pos_val

            if 'Scale' in ani:
                s, time_nodes = ani.get('Scale')
                
                scale_unit = typed_kwargs['scale_unit']
                scale_reverse = typed_kwargs['scale_reverse']
                scale_ratio = typed_kwargs['scale_ratio']
                
                if isinstance(scale_unit, tuple):
                    scale_values = []
                    for i, unit in enumerate(scale_unit):
                        reverse_val = scale_reverse[i] if isinstance(scale_reverse, tuple) else scale_reverse
                        ratio_val = scale_ratio[i] if isinstance(scale_ratio, tuple) else scale_ratio
                        val = self._get_seg_result(s[unit], nowtime, time_nodes) * ratio_val
                        val = -val if reverse_val else val
                        scale_values.append(val)
                    dic['scale'] = tuple(scale_values)
                else:
                    reverse_val = scale_reverse if isinstance(scale_reverse, bool) else scale_reverse[0]
                    ratio_val = scale_ratio if isinstance(scale_ratio, (int, float)) else scale_ratio[0]
                    val = self._get_seg_result(s[scale_unit], nowtime, time_nodes) * ratio_val
                    val = -val if reverse_val else val
                    dic['scale'] = val

            if 'Float' in ani:
                f, time_nodes = ani.get('Float')
                if isinstance(f, list):
                    float_val = self._get_seg_result(f, nowtime, time_nodes)
                    dic['float'] = float_val.item() if isinstance(float_val, np.ndarray) else float_val
            else:
                float_val = 0.0

            events = self.events.get_events(nowtime, time_reverse=typed_kwargs['event_time_reverse'])
            for event in events:
                regstered_event = self.registered_events.get(event[0], (lambda: None, ()))
                parameters = [event[1][arg] for arg in regstered_event[1]]
                regstered_event[0](*parameters)
            dic['events'] = events

            return dic, True
        else:
            self.events.reset_events()
            return {}, False

    def _get_seg_result(self, segments: Any, t: float, time_nodes: Optional[np.ndarray] = None) -> float:
        """Binary search to find segmented interpolation result using Numba acceleration"""
        if not segments:
            return 0.0
        
        segment_index = binary_search_segment_index(time_nodes, t)
        return segments[segment_index](t)

    def return_default(self,
                       default_value: float = 0.0, default_scale=1.0,
                       **kwargs: Union[str, bool, Tuple, float]) -> Tuple[Dict[str, Any], bool]:

        typed_kwargs = type_kwargs(**kwargs)

        dic: Dict[str, Any] = {}
        ani = self.anim[typed_kwargs['path']]
        if 'Euler' in ani:
            euler_unit = typed_kwargs['euler_unit']
            dic['euler'] = tuple(default_value for _ in euler_unit) if isinstance(euler_unit, tuple) else default_value

        if 'Rotation' in ani:
            rotation_unit = typed_kwargs['rotation_unit']
            dic['rotation'] = tuple(default_value for _ in rotation_unit) if isinstance(rotation_unit, tuple) else default_value

        if 'Position' in ani:
            position_unit = typed_kwargs['position_unit']
            if isinstance(position_unit, tuple):
                dic['position'] = tuple(default_value for _ in position_unit)
            else:
                dic['position'] = default_value

        if 'Scale' in ani:
            scale_unit = typed_kwargs['scale_unit']
            if isinstance(scale_unit, tuple):
                dic['scale'] = tuple(default_scale for _ in scale_unit)
            else:
                dic['scale'] = default_scale

        if 'Float' in ani:
            dic['float'] = default_value
        else:
            float_val = 0.0

        dic['playable'] = False

        return dic, False
    
    def sample_range(self, sample_rate=0.01, t_start=None, t_end=None, **kwargs):
        t_start = 0.0 if t_start is None else t_start
        t_end = self.stop_time if t_end is None else t_end
        sample_points = {t: self.play_frame(t, **kwargs)[0] for t in np.arange(t_start, t_end, sample_rate)}
        return sample_points
    
    def add_event(self, delay, *kwargs):
        self.events.add_event(delay, *kwargs)

    def register_event(self, function_name: str, function: Callable, args: Tuple[Literal['data', 'floatParameter', 'intParameter', 'messageOptions'], ...] = ()):
        self.registered_events[function_name] = (function, args)