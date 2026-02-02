from functools import lru_cache

from parse_yaml import parse_anim
from cache_yaml import load_yaml


@lru_cache(maxsize=64)
def load_anim(path):
    anim_json = load_yaml(path)
    anim, stop_time = parse_anim(anim_json)
    return anim, stop_time


class AnimationPlayer:
    def __init__(self, path, stop_time=None):
        self.anim, self.stop_time = load_anim(path)
        if stop_time:
            self.stop_time = stop_time

    def play_frame(self,
             nowtime,
             path='general',
             timeReverse=False,
             Eunit='z',
             Runit='w',
             Punit=('x', 'y'),
             Preverse=(False, False),
             Pratio=(1, 1)):

        nowtime1 = nowtime
        if timeReverse:
            nowtime = self.stop_time - nowtime
        if nowtime1 <= self.stop_time:
            dic = {}
            ani = self.anim[path]
            if 'Euler' in ani:
                e = ani.get('Euler')
                euler = self._get_seg_result(e[Eunit], nowtime)
                dic['euler'] = euler

            if 'Rotation' in ani:
                r = ani.get('Rotation')
                rotation = self._get_seg_result(r[Runit], nowtime)
                dic['rotation'] = rotation

            if 'Position' in ani:
                p = ani.get('Position')
                position = (self._get_seg_result(p[Punit[0]], nowtime) / 1 * Pratio[0],
                            self._get_seg_result(p[Punit[1]], nowtime) / 1 * Pratio[1])
                position = tuple(-position[x] if Preverse[x] else position[x] for x in (0, 1))
                dic['position'] = position

            if 'Scale' in ani:
                s = ani.get('Scale')
                scale = (self._get_seg_result(s['x'], nowtime), self._get_seg_result(s['y'], nowtime))
                dic['scale'] = scale

            if 'Float' in ani:
                f = ani.get('Float')
                if isinstance(f, list):
                    float = self._get_seg_result(f, nowtime)
                    dic['float'] = float
            else:
                float = 0.0
            return dic, True
        else:
            return {}, False

    def _get_seg_result(self, segments, t):
        """二分法查找分段插值结果"""
        if not segments:
            return 0

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

        return segments[-1](t)  # 边界情况

    def return_default(self,
                   default_value = 0.0,
                   path='general',
                   timeReverse=False,
                   Eunit='x',
                   Runit='w',
                   Punit=('x', 'y'),
                   Preverse=(False, False),
                   Pratio=(1, 1)):

        dic = {}
        ani = self.anim[path]
        if 'Euler' in ani:
            dic['euler'] = default_value

        if 'Rotation' in ani:
            dic['rotation'] = default_value

        if 'Position' in ani:
            dic['position'] = (default_value, default_value)

        if 'Scale' in ani:
            dic['scale'] = (default_value, default_value)

        if 'Float' in ani:
            dic['float'] = default_value
        else:
            float = 0.0

        return dic, False

if __name__ == '__main__':
    an = AnimationPlayer('examples/AnimationClip/T.anim')
    dic = an.play_frame(0.83, path='general')
    print(dic)
