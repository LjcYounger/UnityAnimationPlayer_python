#cache_yaml
import os
import json
import tempfile
import hashlib
from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True
yaml.constructor.ignore_aliases = True


def _str_constructor(loader, node):
    if node.tag == 'tag:yaml.org,2002:bool' and node.value == 'y':
        return 'y'
    return loader.construct_scalar(node)


# 防止yaml把"y"解析成True
yaml.constructor.add_constructor('tag:yaml.org,2002:bool', _str_constructor)

temp_folder_path = os.path.join(tempfile.gettempdir(), 'DesktopLobby')
os.makedirs(temp_folder_path, exist_ok=True)


def _get_file_sha256(file_path):
    """计算文件的SHA256哈希值"""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # 逐块读取文件以避免大文件内存问题
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return None


def _save_cache_metadata(json_path, sha256_hash):
    """保存缓存元数据（SHA256哈希）"""
    metadata_path = json_path + '.metadata'
    try:
        with open(metadata_path, 'w') as f:
            json.dump({'sha256': sha256_hash}, f)
    except Exception as e:
        print(f"[Warning]Failed to save cache metadata: {e}")


def _load_cache_metadata(json_path):
    """加载缓存元数据"""
    metadata_path = json_path + '.metadata'
    try:
        with open(metadata_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def load_yaml(path: str, cache=True):
    """加载并缓存yaml，使用SHA256验证文件一致性"""
    # 构建缓存json路径
    json_path = os.path.join(temp_folder_path, path.rsplit('.', 1)[0] + '.json')

    # 计算源文件的SHA256
    source_sha256 = _get_file_sha256(path)
    if source_sha256 is None:
        raise FileNotFoundError(f"Source file not found: {path}")

    try:
        # 检查缓存是否存在且有效
        metadata = _load_cache_metadata(json_path)

        if (metadata and
                metadata.get('sha256') == source_sha256 and
                os.path.exists(json_path)):

            # 缓存有效，直接读取
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"[DEBUG]Loaded cached data for: {path}")
            return data
        else:
            # 缓存无效或不存在，重新生成
            print(f"[WARNING]Cache invalid or missing, regenerating for: {path}")
            raise FileNotFoundError("Cache needs regeneration")

    except (FileNotFoundError, json.JSONDecodeError):
        # 缓存文件不存在或损坏，重新生成
        with open(path, 'r', encoding='utf-8') as y:
            data = yaml.load(y)

        if cache:
            # 确保目录存在
            os.makedirs(os.path.dirname(json_path), exist_ok=True)

            # 保存JSON缓存
            with open(json_path, 'w', encoding='utf-8') as j:
                json_data = json.dumps(data, ensure_ascii=False, indent=2)
                j.write(json_data)

            # 保存元数据（SHA256）
            _save_cache_metadata(json_path, source_sha256)
            print(f"[DEBUG]Cached data regenerated for: {path}")

        return json.loads(json.dumps(data))


def clear_yaml_cache(path: str = None):
    """清除YAML缓存文件"""
    if path:
        # 清除特定文件的缓存
        json_path = os.path.join(temp_folder_path, path.rsplit('.', 1)[0] + '.json')
        metadata_path = json_path + '.metadata'

        for cache_path in [json_path, metadata_path]:
            try:
                if os.path.exists(cache_path):
                    os.remove(cache_path)
                    print(f"[DEBUG]Removed cache: {cache_path}")
            except Exception as e:
                print(f"[ERROR]Error removing cache {cache_path}: {e}")
    else:
        # 清除所有缓存
        import shutil
        try:
            if os.path.exists(temp_folder_path):
                shutil.rmtree(temp_folder_path)
                os.makedirs(temp_folder_path, exist_ok=True)
                print("[DEBUG]Cleared all YAML cache")
        except Exception as e:
            print(f"[ERROR]Error clearing cache: {e}")


def get_cache_info(path: str):
    """获取缓存信息"""
    json_path = os.path.join(temp_folder_path, path.rsplit('.', 1)[0] + '.json')
    metadata = _load_cache_metadata(json_path)
    source_sha256 = _get_file_sha256(path)

    cache_exists = os.path.exists(json_path)
    metadata_exists = metadata is not None
    is_valid = metadata and metadata.get('sha256') == source_sha256

    return {
        'source_sha256': source_sha256,
        'cached_sha256': metadata.get('sha256') if metadata else None,
        'cache_exists': cache_exists,
        'metadata_exists': metadata_exists,
        'is_valid': is_valid,
        'json_path': json_path
    }










#parse_yaml
from scipy.interpolate import CubicHermiteSpline
import numpy as np

def piecewise_hermite(x_points, y_points, in_slopes, out_slopes, in_weights, out_weights, tangentMode, weightedMode):
    # 转为 numpy 数组
    x_points = np.array(x_points)
    y_points = np.array(y_points)
    in_slopes = np.array(in_slopes)
    out_slopes = np.array(out_slopes)
    in_weights = np.array(in_weights)
    out_weights = np.array(out_weights)
    tangentMode = np.array(tangentMode)
    weightedMode = np.array(weightedMode)

    # 加权模式处理
    if np.all(weightedMode == 0.0):
        in_slopes = np.clip(in_slopes, -1e8, 1e8)
        out_slopes = np.clip(out_slopes, -1e8, 1e8)
        in_slopes *= in_weights
        out_slopes *= out_weights

    segments = []

    # 判断是否分段（tangentMode == 1 表示该点是“可连接”的内部点）
    # 我们按“断点”分段：tangentMode != 1 的点作为分段边界
    break_points = np.where(tangentMode != 1.0)[0]  # 不连续的点
    indices = [0] + list(break_points) + [len(x_points)-1]
    indices = sorted(set(indices))

    for i in range(len(indices) - 1):
        start = indices[i]
        end = indices[i+1] + 1  # 包含 end 点
        x_seg = x_points[start:end]
        y_seg = y_points[start:end]
        if len(x_seg) < 2:
            continue

        # 使用平均斜率（或选择 in/out）
        slopes_seg = (in_slopes[start:end] + out_slopes[start:end]) / 2

        try:
            cs = CubicHermiteSpline(x_seg, y_seg, slopes_seg)
            segments.append(cs)
        except Exception as e:
            segments.append(None)

    return segments

def _parse_m_Curve(m_Curve_list):
    """解析一个m_Curve块，并进行插值处理"""
    #m_Curve内的所有参数
    parameter_keys = list(m_Curve_list[0].keys())
    parameter_keys.remove("serializedVersion")
    parameter_dict = {}
    for key in parameter_keys:
        if type(m_Curve_list[0][key]) == dict:
            parameter_dict [key] = {x: tuple(0 if curve[key][x] in ('Infinity', '-Infinity') else curve[key][x] for curve in m_Curve_list) for x in m_Curve_list[0][key].keys()}
        else:
            parameter_dict [key] = tuple(0 if curve[key] in ('Infinity', '-Infinity') else curve[key] for curve in m_Curve_list)
    #把parameter_dict中的数据进行插值，x: time, y: values
    if type(parameter_dict["value"]) == dict:
        #依次传入参数进行插值
        interpolation_list = {x: piecewise_hermite(parameter_dict["time"], *tuple(parameter_dict[para][x] for para in ("value", "inSlope", "outSlope", "inWeight", "outWeight")), parameter_dict["tangentMode"], parameter_dict["weightedMode"]) for x in parameter_dict["value"].keys()}
    else:
        #依次传入参数进行插值
        interpolation_list = piecewise_hermite(parameter_dict["time"], *tuple(parameter_dict[para] for para in ("value", "inSlope", "outSlope", "inWeight", "outWeight")), parameter_dict["tangentMode"], parameter_dict["weightedMode"])
    max_time = max(parameter_dict["time"])
    return interpolation_list, max_time

def _parse_curve(m_XCurves):
    """
    解析一个m_XCurve块
    输出：{"path": "m_Curve_interpolation", ...}
    """
    output = {}
    general_times = 0
    max_times=[]
    for m_XCurve in m_XCurves:
        path = m_XCurve["path"]
        if path == None:
            path = 'general' if general_times == 0 else f"general({general_times})"
            general_times += 1
        else:
            path = str(path)
        parse_output, max_time = _parse_m_Curve(m_XCurve["curve"]["m_Curve"])
        output [path] = parse_output
        max_times.append(max_time)
    max_time_ = max(max_times)
    return output, max_time


def parse_anim(anim_dict):
    anim_dict = anim_dict["AnimationClip"]
    stop_time = anim_dict["m_AnimationClipSettings"]["m_StopTime"]
    m_XCurveses = ("m_RotationCurves", "m_CompressedRotationCurves", "m_EulerCurves", "m_PositionCurves", "m_ScaleCurves")
    paths = {}
    for m_XCurves in m_XCurveses:
        m_XCurves_list = anim_dict[m_XCurves]
        if m_XCurves_list:
            m_XCurves_dict, max_time = _parse_curve(m_XCurves_list)
            for path_key, m_Curve_interpolation in m_XCurves_dict.items():
                if not path_key in paths.keys():
                    paths[path_key] = {}
                paths[path_key][m_XCurves[2:-6]] = m_Curve_interpolation
            if stop_time == 1 and type(stop_time) == int:
                stop_time = max_time
    return paths, stop_time






#animation_player
from functools import lru_cache


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
             Eunit='x',
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
    an = AnimationPlayer('examples/AnimationClip/UIAni_Emo_Sc_Dot.anim')
    dic = an.play_frame(0.2, path='1')
    print(dic)
