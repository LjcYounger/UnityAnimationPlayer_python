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