from functools import lru_cache
from typing import Dict, Any, Tuple, Union, Optional
from dataclasses import asdict

import numpy as np

from .parse_yaml import parse_anim
from .cache_yaml import load_yaml

from .kwargs import PlayKwargs, PlayKwargsDict

@lru_cache(maxsize=64)
def load_anim(path: str) -> Tuple[Dict[str, Any], float]:
    anim_json = load_yaml(path)
    anim, stop_time = parse_anim(anim_json)
    return anim, stop_time

def type_kwargs(**kwargs) -> PlayKwargsDict:

    default_kwargs = PlayKwargs()
    merged_kwargs = {**asdict(default_kwargs), **kwargs}
        
    typed_kwargs: PlayKwargsDict = {
        'path': str(merged_kwargs['path']),
        'time_reverse': bool(merged_kwargs['time_reverse']),
        'euler_unit': merged_kwargs['euler_unit'],
        'rotation_unit': merged_kwargs['rotation_unit'],
        'position_unit': merged_kwargs['position_unit'],
        'position_reverse': merged_kwargs['position_reverse'],
        'position_ratio': merged_kwargs['position_ratio'],
        'scale_unit': merged_kwargs['scale_unit'],
        'scale_reverse': merged_kwargs['scale_reverse'],
        'scale_ratio': merged_kwargs['scale_ratio']
    }
    return typed_kwargs


class AnimationPlayer:
    def __init__(self, path: str, stop_time: Optional[float] = None):
        self.anim, self.stop_time = load_anim(path)
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
                e = ani.get('Euler')

                euler_unit = typed_kwargs['euler_unit']
                if isinstance(euler_unit, tuple):
                    euler = tuple(self._get_seg_result(e[unit], nowtime) for unit in euler_unit)
                else:
                    euler = self._get_seg_result(e[euler_unit], nowtime)
                dic['euler'] = euler

            if 'Rotation' in ani:
                r = ani.get('Rotation')

                rotation_unit = typed_kwargs['rotation_unit']
                if isinstance(rotation_unit, tuple):
                    rotation = tuple(self._get_seg_result(r[unit], nowtime) for unit in rotation_unit)
                else:
                    rotation = self._get_seg_result(r[rotation_unit], nowtime)
                dic['rotation'] = rotation

            if 'Position' in ani:
                p = ani.get('Position')

                position_unit = typed_kwargs['position_unit']
                position_reverse = typed_kwargs['position_reverse']
                position_ratio = typed_kwargs['position_ratio']
                
                if isinstance(position_unit, tuple):

                    position_values = []
                    for i, unit in enumerate(position_unit):

                        reverse_val = position_reverse[i] if isinstance(position_reverse, tuple) else position_reverse
                        ratio_val = position_ratio[i] if isinstance(position_ratio, tuple) else position_ratio
                        pos_val = self._get_seg_result(p[unit], nowtime) * ratio_val
                        pos_val = -pos_val if reverse_val else pos_val
                        position_values.append(pos_val)
                    dic['position'] = tuple(position_values)
                else:

                    reverse_val = position_reverse if isinstance(position_reverse, bool) else position_reverse[0]
                    ratio_val = position_ratio if isinstance(position_ratio, (int, float)) else position_ratio[0]
                    pos_val = self._get_seg_result(p[position_unit], nowtime) * ratio_val
                    pos_val = -pos_val if reverse_val else pos_val
                    dic['position'] = pos_val

            if 'Scale' in ani:
                s = ani.get('Scale')
                
                scale_unit = typed_kwargs['scale_unit']
                scale_reverse = typed_kwargs['scale_reverse']
                scale_ratio = typed_kwargs['scale_ratio']
                
                if isinstance(scale_unit, tuple):
                    scale_values = []
                    for i, unit in enumerate(scale_unit):
                        reverse_val = scale_reverse[i] if isinstance(scale_reverse, tuple) else scale_reverse
                        ratio_val = scale_ratio[i] if isinstance(scale_ratio, tuple) else scale_ratio
                        val = self._get_seg_result(s[unit], nowtime) * ratio_val
                        val = -val if reverse_val else val
                        scale_values.append(val)
                    dic['scale'] = tuple(scale_values)
                else:
                    reverse_val = scale_reverse if isinstance(scale_reverse, bool) else scale_reverse[0]
                    ratio_val = scale_ratio if isinstance(scale_ratio, (int, float)) else scale_ratio[0]
                    val = self._get_seg_result(s[scale_unit], nowtime) * ratio_val
                    val = -val if reverse_val else val
                    dic['scale'] = val

            if 'Float' in ani:
                f = ani.get('Float')
                if isinstance(f, list):
                    float_val = self._get_seg_result(f, nowtime)
                    dic['float'] = float_val
            else:
                float_val = 0.0
            return dic, True
        else:
            return {}, False

    def _get_seg_result(self, segments: Any, t: float) -> float:
        """Binary search to find segmented interpolation result"""
        if not segments:
            return 0.0

        left, right = 0, len(segments) - 1
        while left <= right:
            mid = (left + right) // 2
            seg = segments[mid]
            if t < seg.x[0]:
                right = mid - 1
            elif t > seg.x[-1]:
                left = mid + 1
            else:
                return seg(t)

        return segments[-1](t)  # Boundary case

    def return_default(self,
                       default_value: float = 0.0,
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
                dic['scale'] = tuple(default_value for _ in scale_unit)
            else:
                dic['scale'] = default_value

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