from scipy.interpolate import CubicHermiteSpline, interp1d
import numpy as np

# ===== 新增：统一插值段类 =====
class MixedSegment:
    def __init__(self, x_start, x_end, interpolator):
        self.x = np.array([x_start, x_end], dtype=float)
        self.x_interval = (x_start, x_end)
        self._interp = interpolator  # 可调用对象
    
    def __call__(self, x):
        return self._interp(x)
    
    def covers(self, x):
        a, b = self.x_interval
        return (x >= a) & (x <= b)

# ===== 修改 piecewise_hermite 函数 =====
def piecewise_hermite(x_points, y_points, in_slopes, out_slopes, in_weights, out_weights, tangentMode, weightedMode):
    x_points = np.array(x_points, dtype=float)
    y_points = np.array(y_points, dtype=float)
    n = len(x_points)
    if n < 2:
        return []

    # === 解析斜率：将 'Infinity' / '-Infinity' 转为 np.inf / -np.inf ===
    def parse_slope(s):
        if s == 'Infinity':
            return np.inf
        elif s == '-Infinity':
            return -np.inf
        else:
            return float(s)

    in_sl_raw = np.array([parse_slope(s) for s in in_slopes])
    out_sl_raw = np.array([parse_slope(s) for s in out_slopes])

    # === 加权处理（仅当 weightedMode 全为 0）===
    if np.all(np.array(weightedMode, dtype=float) == 0.0):
        in_weights = np.array(in_weights, dtype=float)
        out_weights = np.array(out_weights, dtype=float)

        # 转为 float 数组（inf 会保留为 np.inf）
        in_sl = np.array(in_sl_raw, dtype=float)
        out_sl = np.array(out_sl_raw, dtype=float)

        # 创建有限值掩码
        finite_in = np.isfinite(in_sl)
        finite_out = np.isfinite(out_sl)

        # 只对有限值应用 clip 和权重
        in_sl[finite_in] = np.clip(in_sl[finite_in] * in_weights[finite_in], -1e8, 1e8)
        out_sl[finite_out] = np.clip(out_sl[finite_out] * out_weights[finite_out], -1e8, 1e8)

        # inf / -inf 保持不变（已自动保留）
    else:
        in_sl = np.array(in_sl_raw, dtype=float)
        out_sl = np.array(out_sl_raw, dtype=float)

    tangentMode = np.array(tangentMode, dtype=float)

    segments = []

    # === 按 tangentMode != 1 分段（断点）===
    break_indices = np.where(tangentMode != 1.0)[0]
    indices = [0] + list(break_indices) + [n - 1]
    indices = sorted(set(indices))

    for seg_start_idx in range(len(indices) - 1):
        i0 = indices[seg_start_idx]
        i1 = indices[seg_start_idx + 1]  # 连续段：[i0, i1]（包含）

        if i1 <= i0:
            continue

        # 提取子段数据
        sub_x = x_points[i0:i1+1]
        sub_y = y_points[i0:i1+1]
        sub_in = in_sl[i0:i1+1]
        sub_out = out_sl[i0:i1+1]

        num_intervals = len(sub_x) - 1
        if num_intervals <= 0:
            continue

        # === 预处理每一段 [k, k+1] 是否为常量 ===
        for k in range(num_intervals):
            x0, x1 = sub_x[k], sub_x[k+1]
            y0, y1 = sub_y[k], sub_y[k+1]
            out_slope_k = sub_out[k]      # 控制 [x_k, x_{k+1}]
            in_slope_k1 = sub_in[k+1]     # 也控制 [x_k, x_{k+1}]

            use_constant = False
            const_value = None

            # 🔥 优先检查 outSlope[k] 和 inSlope[k+1] 是否为 inf
            if np.isinf(out_slope_k):
                use_constant = True
                const_value = y0 if out_slope_k == np.inf else y1
            elif np.isinf(in_slope_k1):
                use_constant = True
                const_value = y0 if in_slope_k1 == np.inf else y1
            if use_constant:
                # 创建常量插值函数（向量化安全）
                interpolator = lambda x, val=const_value: np.full_like(x, val, dtype=float)
            else:
                #PROBLEM
                # 使用 Hermite：每个端点导数 = (in + out) / 2
                slope0 = np.asarray((sub_out[k], sub_in[k]))
                slope0 = np.mean(slope0[np.isfinite(slope0)])
                slope1 = np.asarray((sub_out[k+1], sub_in[k+1]))
                slope1 = np.mean(slope1[np.isfinite(slope1)])

                # 🔒 安全兜底：如果斜率仍含 inf（理论上不该有），转常量
                if not (np.isfinite(slope0) and np.isfinite(slope1)):
                    interpolator = lambda x, val=y0: np.full_like(x, val, dtype=float)
                else:
                    try:
                        hermite = CubicHermiteSpline([x0, x1], [y0, y1], [slope0, slope1])
                        interpolator = hermite
                    except Exception:
                        # fallback to linear
                        interpolator = interp1d([x0, x1], [y0, y1], kind='linear', fill_value="extrapolate")

            segments.append(MixedSegment(x0, x1, interpolator))

    return segments


# ===== 修改 _parse_m_Curve：适配新返回类型 =====
def _parse_m_Curve(m_Curve_list):
    """解析一个m_Curve块，并进行插值处理"""
    parameter_keys = list(m_Curve_list[0].keys())
    parameter_keys.remove("serializedVersion")
    parameter_dict = {}
    for key in parameter_keys:
        if isinstance(m_Curve_list[0][key], dict):
            parameter_dict[key] = {
                x: tuple(curve[key][x] for curve in m_Curve_list)
                for x in m_Curve_list[0][key].keys()
            }
        else:
            parameter_dict[key] = tuple(curve[key] for curve in m_Curve_list)

    max_time = max(parameter_dict["time"])

    if isinstance(parameter_dict["value"], dict):
        interpolation_list = {}
        for comp in parameter_dict["value"].keys():
            args = (
                parameter_dict["time"],
                parameter_dict["value"][comp],
                parameter_dict["inSlope"][comp],
                parameter_dict["outSlope"][comp],
                parameter_dict["inWeight"][comp],
                parameter_dict["outWeight"][comp],
                parameter_dict["tangentMode"],
                parameter_dict["weightedMode"]
            )
            interpolation_list[comp] = piecewise_hermite(*args)
    else:
        args = (
            parameter_dict["time"],
            parameter_dict["value"],
            parameter_dict["inSlope"],
            parameter_dict["outSlope"],
            parameter_dict["inWeight"],
            parameter_dict["outWeight"],
            parameter_dict["tangentMode"],
            parameter_dict["weightedMode"]
        )
        interpolation_list = piecewise_hermite(*args)

    return interpolation_list, max_time


# ===== 保留其他函数不变 =====
def _parse_curve(m_XCurves):
    output = {}
    general_times = 0
    max_times = []
    for m_XCurve in m_XCurves:
        path = m_XCurve["path"]
        if path is None:
            path = 'general' if general_times == 0 else f"general({general_times})"
            general_times += 1
        else:
            path = str(path)
        parse_output, max_time = _parse_m_Curve(m_XCurve["curve"]["m_Curve"])
        output[path] = parse_output
        max_times.append(max_time)
    max_time_ = max(max_times) if max_times else 0
    return output, max_time_


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
                if path_key not in paths:
                    paths[path_key] = {}
                paths[path_key][m_XCurves[2:-6]] = m_Curve_interpolation
            if stop_time == 1 and type(stop_time) == int:
                stop_time = max_time
    return paths, stop_time