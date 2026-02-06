from functools import lru_cache
from typing import Dict, Any, Tuple, Union, Optional
from dataclasses import asdict

from parse_yaml import parse_anim
from cache_yaml import load_yaml

from kwargs import PlayKwargs, PlayKwargsDict

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
        'timeReverse': bool(merged_kwargs['timeReverse']),
        'Eunit': merged_kwargs['Eunit'],
        'Runit': merged_kwargs['Runit'],
        'Punit': merged_kwargs['Punit'],
        'Preverse': merged_kwargs['Preverse'],
        'Pratio': merged_kwargs['Pratio']
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
        if typed_kwargs['timeReverse']:
            nowtime = self.stop_time - nowtime
        if nowtime1 <= self.stop_time:
            dic: Dict[str, Any] = {}
            ani = self.anim[typed_kwargs['path']]
            if 'Euler' in ani:
                e = ani.get('Euler')
                # Handle Eunit as single string or tuple
                eunit = typed_kwargs['Eunit']
                if isinstance(eunit, tuple):
                    euler = tuple(self._get_seg_result(e[unit], nowtime) for unit in eunit)
                else:
                    euler = self._get_seg_result(e[eunit], nowtime)
                dic['euler'] = euler

            if 'Rotation' in ani:
                r = ani.get('Rotation')
                # Handle Runit as single string or tuple
                runit = typed_kwargs['Runit']
                if isinstance(runit, tuple):
                    rotation = tuple(self._get_seg_result(r[unit], nowtime) for unit in runit)
                else:
                    rotation = self._get_seg_result(r[runit], nowtime)
                dic['rotation'] = rotation

            if 'Position' in ani:
                p = ani.get('Position')
                # Handle Punit, Preverse, Pratio as single value or tuple
                punit = typed_kwargs['Punit']
                preverse = typed_kwargs['Preverse']
                pratio = typed_kwargs['Pratio']
                
                if isinstance(punit, tuple):
                    # Punit is tuple case - apply values sequentially
                    position_values = []
                    for i, unit in enumerate(punit):
                        # Get corresponding reverse and ratio values by index
                        reverse_val = preverse[i] if isinstance(preverse, tuple) else preverse
                        ratio_val = pratio[i] if isinstance(pratio, tuple) else pratio
                        pos_val = self._get_seg_result(p[unit], nowtime) * ratio_val
                        pos_val = -pos_val if reverse_val else pos_val
                        position_values.append(pos_val)
                    dic['position'] = tuple(position_values)
                else:
                    # Punit is single string case - apply same values to all coordinates
                    reverse_val = preverse if isinstance(preverse, bool) else preverse[0]
                    ratio_val = pratio if isinstance(pratio, (int, float)) else pratio[0]
                    pos_val = self._get_seg_result(p[punit], nowtime) * ratio_val
                    pos_val = -pos_val if reverse_val else pos_val
                    dic['position'] = pos_val

            if 'Scale' in ani:
                s = ani.get('Scale')
                scale = (self._get_seg_result(s['x'], nowtime), self._get_seg_result(s['y'], nowtime))
                dic['scale'] = scale

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
            eunit = typed_kwargs['Eunit']
            dic['euler'] = tuple(default_value for _ in eunit) if isinstance(eunit, tuple) else default_value

        if 'Rotation' in ani:
            runit = typed_kwargs['Runit']
            dic['rotation'] = tuple(default_value for _ in runit) if isinstance(runit, tuple) else default_value

        if 'Position' in ani:
            punit = typed_kwargs['Punit']
            if isinstance(punit, tuple):
                dic['position'] = tuple(default_value for _ in punit)
            else:
                dic['position'] = default_value

        if 'Scale' in ani:
            dic['scale'] = (default_value, default_value)

        if 'Float' in ani:
            dic['float'] = default_value
        else:
            float_val = 0.0

        return dic, False

if __name__ == '__main__':
    an = AnimationPlayer('examples/AnimationClip/T.anim')
    dic = an.play_frame(0.83, path='general', Punit=('x', 'y', 'z'), Pratio=(0.01, 100, 1))
    print(dic)
    dic = an.play_frame(0.245, path='general', Punit='y')
    print(dic)