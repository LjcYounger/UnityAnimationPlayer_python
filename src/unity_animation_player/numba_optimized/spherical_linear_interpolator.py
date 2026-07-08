from ..config import USE_JIT
import numpy as np

if USE_JIT:
    try:
        from numba import njit, float64
        from numba.experimental import jitclass
    except:
        def njit(*args, **kwargs):
            if len(args) == 1 and callable(args[0]) and not kwargs:
                return args[0]
            def decorator(f):
                return f
            return decorator
        jitclass = lambda spec: lambda cls: cls
        float64 = float
else:
    def njit(*args, **kwargs):
        if len(args) == 1 and callable(args[0]) and not kwargs:
            return args[0]
        def decorator(f):
            return f
        return decorator
    jitclass = lambda spec: lambda cls: cls
    float64 = float


# ==================== 工具函数 ====================

@njit
def _clamp(value: float, min_val: float, max_val: float) -> float:
    """限制值在指定范围内"""
    if value < min_val:
        return min_val
    elif value > max_val:
        return max_val
    return value


@njit
def _axis_angle_to_quaternion(axis_x: float, axis_y: float, axis_z: float, angle_deg: float) -> tuple:
    """
    轴角（度）转四元数
    
    参数:
        axis_x, axis_y, axis_z: 旋转轴向量
        angle_deg: 旋转角度（度）
    
    返回:
        (x, y, z, w) 四元数分量
    """
    half = np.radians(angle_deg) * 0.5
    s = np.sin(half)
    c = np.cos(half)
    
    # 归一化轴向量
    length = np.sqrt(axis_x*axis_x + axis_y*axis_y + axis_z*axis_z)
    if length > 1e-15:
        axis_x /= length
        axis_y /= length
        axis_z /= length
    
    x = axis_x * s
    y = axis_y * s
    z = axis_z * s
    w = c
    
    return (x, y, z, w)


@njit
def _quaternion_to_axis_angle(x: float, y: float, z: float, w: float) -> tuple:
    """
    四元数转轴角（度）
    
    返回:
        (axis_x, axis_y, axis_z, angle_deg)
    """
    # 归一化
    length = np.sqrt(x*x + y*y + z*z + w*w)
    if length > 1e-15:
        x /= length
        y /= length
        z /= length
        w /= length
    
    # 限制 w 范围
    if w > 1.0:
        w = 1.0
    elif w < -1.0:
        w = -1.0
    
    angle_rad = 2.0 * np.arccos(w)
    angle_deg = np.degrees(angle_rad)
    
    sin_half = np.sin(angle_rad / 2.0)
    
    if abs(sin_half) < 1e-10:
        # 零旋转，返回默认轴
        return (1.0, 0.0, 0.0, 0.0)
    
    axis_x = x / sin_half
    axis_y = y / sin_half
    axis_z = z / sin_half
    
    return (axis_x, axis_y, axis_z, angle_deg)


@njit
def _euler_to_quaternion(euler_x: float, euler_y: float, euler_z: float) -> tuple:
    """
    将欧拉角（度）转换为四元数
    
    旋转顺序：Z -> X -> Y (Unity 默认顺序)
    
    参数:
        euler_x: X轴旋转角度（度）
        euler_y: Y轴旋转角度（度）
        euler_z: Z轴旋转角度（度）
    
    返回:
        (x, y, z, w) 四元数分量
    """
    # 将角度转换为弧度并除以2
    cx = np.cos(np.radians(euler_x) * 0.5)
    sx = np.sin(np.radians(euler_x) * 0.5)
    cy = np.cos(np.radians(euler_y) * 0.5)
    sy = np.sin(np.radians(euler_y) * 0.5)
    cz = np.cos(np.radians(euler_z) * 0.5)
    sz = np.sin(np.radians(euler_z) * 0.5)
    
    # Unity 旋转顺序 ZXY 的四元数计算公式
    x = sx * cy * cz + cx * sy * sz
    y = cx * sy * cz - sx * cy * sz
    z = cx * cy * sz - sx * sy * cz
    w = cx * cy * cz + sx * sy * sz
    
    return (x, y, z, w)


@njit
def _quaternion_to_euler(x: float, y: float, z: float, w: float) -> tuple:
    """
    将四元数转换为欧拉角（度）
    
    返回顺序：X, Y, Z (Unity 默认顺序)
    
    参数:
        x, y, z, w: 四元数的四个分量
    
    返回:
        (euler_x, euler_y, euler_z) 欧拉角（度）
    """
    # 归一化四元数
    length = np.sqrt(x*x + y*y + z*z + w*w)
    if length > 1e-15:
        x /= length
        y /= length
        z /= length
        w /= length
    
    # 计算 roll (x-axis rotation)
    sinr_cosp = 2.0 * (w * x + y * z)
    cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
    euler_x = np.degrees(np.arctan2(sinr_cosp, cosr_cosp))
    
    # 计算 pitch (y-axis rotation)
    sinp = 2.0 * (w * y - z * x)
    if abs(sinp) >= 1.0:
        euler_y = np.degrees(np.copysign(np.pi / 2.0, sinp))
    else:
        euler_y = np.degrees(np.arcsin(sinp))
    
    # 计算 yaw (z-axis rotation)
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    euler_z = np.degrees(np.arctan2(siny_cosp, cosy_cosp))
    
    return (euler_x, euler_y, euler_z)


@njit
def _normalize_angle(angle: float) -> float:
    """将角度规范化到 [-180, 180] 范围"""
    return np.mod(angle + 180.0, 360.0) - 180.0


@njit
def _detect_full_rotation(x0: float, y0: float, z0: float, w0: float,
                          x1: float, y1: float, z1: float, w1: float) -> bool:
    """
    检测两个四元数是否代表一个完整旋转（360°的整数倍）
    
    当两个四元数表示相同朝向但符号相反，且起始四元数接近恒等变换时，
    判定为完整旋转。
    """
    # 计算点积
    dot = x0*x1 + y0*y1 + z0*z1 + w0*w1
    
    # 如果点积接近 -1，说明两个四元数方向相反
    if dot < -0.999:
        # 检查起始四元数是否接近恒等变换 (0,0,0,1) 或 (0,0,0,-1)
        vec_len = x0*x0 + y0*y0 + z0*z0
        if vec_len < 0.001 * 0.001:  # 向量部分接近0
            return True
    
    return False


# ==================== 四元数 SLERP 插值器 ====================

# 定义 SLERP 类的字段类型规范
spec_quaternion_slerp = [
    ('x0', float64),
    ('y0', float64),
    ('z0', float64),
    ('w0', float64),
    ('x1', float64),
    ('y1', float64),
    ('z1', float64),
    ('w1', float64),
    ('t0', float64),
    ('t1', float64),
]

# 定义轴角插值器的字段类型规范
spec_axis_angle = [
    ('axis_x', float64),
    ('axis_y', float64),
    ('axis_z', float64),
    ('angle_start', float64),
    ('angle_total', float64),
    ('t0', float64),
    ('t1', float64),
]


@jitclass(spec_quaternion_slerp)
class _SphericalLinearInterpolator:
    """
    球面线性插值器核心（Numba JIT 编译版本）
    
    用于在两个四元数之间进行球面线性插值（SLERP）。
    这是一个内部类，外部使用 SphericalLinearInterpolation 工厂函数
    """
    
    def __init__(self, x0: float, y0: float, z0: float, w0: float,
                 x1: float, y1: float, z1: float, w1: float,
                 t0: float = 0.0, t1: float = 1.0):
        # 保存起始和结束四元数
        self.x0 = x0
        self.y0 = y0
        self.z0 = z0
        self.w0 = w0
        self.x1 = x1
        self.y1 = y1
        self.z1 = z1
        self.w1 = w1
        # 保存时间范围，支持自动归一化
        self.t0 = t0
        self.t1 = t1
    
    def evaluate(self, t: float) -> tuple:
        """
        计算给定 t 值对应的插值四元数
        
        参数:
            t: 可以是归一化参数 [0, 1] 或实际时间值（如果设置了 t0, t1）
        
        返回:
            (x, y, z, w) 四元数分量
        """
        # 如果设置了时间范围，自动归一化
        if self.t1 != self.t0:
            t_normalized = (t - self.t0) / (self.t1 - self.t0)
            t_normalized = _clamp(t_normalized, 0.0, 1.0)
        else:
            t_normalized = t
        
        return self._slerp_core(t_normalized)
    
    def _slerp_core(self, t: float) -> tuple:
        """
        SLERP 核心计算
        
        球面线性插值公式：
        q(t) = q0 * sin((1-t)*θ) / sin(θ) + q1 * sin(t*θ) / sin(θ)
        """
        x0 = self.x0
        y0 = self.y0
        z0 = self.z0
        w0 = self.w0
        x1 = self.x1
        y1 = self.y1
        z1 = self.z1
        w1 = self.w1
        
        # 计算点积（夹角的余弦值）
        dot = x0*x1 + y0*y1 + z0*z1 + w0*w1
        
        # 如果点积为负，翻转其中一个四元数以选择最短路径
        if dot < 0.0:
            x1 = -x1
            y1 = -y1
            z1 = -z1
            w1 = -w1
            dot = -dot
        
        # 限制点积范围，防止数值误差导致的问题
        if dot > 1.0:
            dot = 1.0
        elif dot < -1.0:
            dot = -1.0
        
        # 计算夹角
        theta_0 = np.arccos(dot)
        sin_theta_0 = np.sin(theta_0)
        
        # 如果夹角非常小，使用线性插值避免除以零
        if abs(sin_theta_0) < 1e-6:
            # 线性插值
            x = x0 + t * (x1 - x0)
            y = y0 + t * (y1 - y0)
            z = z0 + t * (z1 - z0)
            w = w0 + t * (w1 - w0)
            
            # 归一化
            length = np.sqrt(x*x + y*y + z*z + w*w)
            if length > 1e-15:
                x /= length
                y /= length
                z /= length
                w /= length
            
            return (x, y, z, w)
        
        # 计算插值系数
        sin_theta_t = np.sin(t * theta_0)
        sin_theta_1_t = np.sin((1.0 - t) * theta_0)
        
        s0 = sin_theta_1_t / sin_theta_0
        s1 = sin_theta_t / sin_theta_0
        
        # 计算插值后的四元数
        x = s0 * x0 + s1 * x1
        y = s0 * y0 + s1 * y1
        z = s0 * z0 + s1 * z1
        w = s0 * w0 + s1 * w1
        
        return (x, y, z, w)


@jitclass(spec_axis_angle)
class _AxisAngleInterpolator:
    """
    轴角插值器（Numba JIT 编译版本）
    
    用于绕固定轴进行角度插值，解决 SLERP 无法处理 360° 完整旋转的问题。
    所有字段必须在 spec 中预先定义。
    """
    
    def __init__(self, axis_x: float, axis_y: float, axis_z: float, 
                 angle_start: float, angle_total: float,
                 t0: float = 0.0, t1: float = 1.0):
        # 保存轴向量
        self.axis_x = axis_x
        self.axis_y = axis_y
        self.axis_z = axis_z
        # 保存角度信息
        self.angle_start = angle_start
        self.angle_total = angle_total
        # 保存时间范围
        self.t0 = t0
        self.t1 = t1
    
    def evaluate(self, t: float) -> tuple:
        """
        计算给定 t 值对应的插值四元数
        
        参数:
            t: 可以是归一化参数 [0, 1] 或实际时间值（如果设置了 t0, t1）
        
        返回:
            (x, y, z, w) 四元数分量
        """
        # 如果设置了时间范围，自动归一化
        if self.t1 != self.t0:
            t_normalized = (t - self.t0) / (self.t1 - self.t0)
            t_normalized = _clamp(t_normalized, 0.0, 1.0)
        else:
            t_normalized = t
        
        # 计算当前角度
        current_angle = self.angle_start + self.angle_total * t_normalized
        
        # 生成对应的四元数
        return _axis_angle_to_quaternion(self.axis_x, self.axis_y, self.axis_z, current_angle)


def SphericalLinearInterpolation(x0: float, y0: float, z0: float, w0: float,
                                 x1: float, y1: float, z1: float, w1: float,
                                 t0: float = 0.0, t1: float = 1.0, 
                                 force_axis_angle: bool = False):
    """
    球面线性插值器工厂函数
    
    创建并返回一个可调用的插值器对象，用于在两个四元数之间进行插值。
    默认使用 SLERP，当检测到完整旋转（360°）时会自动切换到轴角插值。
    
    参数:
        x0, y0, z0, w0: 起始四元数的四个分量
        x1, y1, z1, w1: 结束四元数的四个分量
        t0, t1: 时间范围（可选），如果提供则自动进行时间归一化
        force_axis_angle: 强制使用轴角插值模式
    
    返回:
        一个可调用对象，接受 t 参数并返回插值后的四元数 (x, y, z, w)
        - 如果提供了 t0, t1：t 可以是实际时间值，会自动归一化
        - 如果未提供 t0, t1：t 应该是归一化参数 [0, 1]
    
    示例:
        >>> # 普通 SLERP 插值
        >>> slerp = SphericalLinearInterpolation(0, 0, 0, 1, 0, 0, 0.7071, 0.7071)
        >>> x, y, z, w = slerp(0.5)
        
        >>> # 360° 完整旋转（自动切换轴角模式）
        >>> slerp = SphericalLinearInterpolation(0, 0, 0, 1, 0, 0, 0, -1)
        >>> x, y, z, w = slerp(0.5)  # 绕 Z 轴旋转 180°
    """
    # 检测是否需要使用轴角插值
    use_axis_angle = force_axis_angle or _detect_full_rotation(x0, y0, z0, w0, x1, y1, z1, w1)
    
    if use_axis_angle:
        # 提取轴角信息
        if abs(x0) < 0.001 and abs(y0) < 0.001 and abs(z0) < 0.001:
            # 起始四元数接近恒等变换，从结束四元数提取轴
            axis_x, axis_y, axis_z, angle_total = _quaternion_to_axis_angle(x1, y1, z1, w1)
            # 如果角度接近360，保留完整旋转
            if abs(angle_total) < 0.1:
                angle_total = 360.0
            interpolator = _AxisAngleInterpolator(axis_x, axis_y, axis_z, 0.0, angle_total, t0, t1)
        else:
            # 一般情况，提取轴角
            axis_x, axis_y, axis_z, angle_0 = _quaternion_to_axis_angle(x0, y0, z0, w0)
            _, _, _, angle_1 = _quaternion_to_axis_angle(x1, y1, z1, w1)
            angle_diff = angle_1 - angle_0
            if abs(angle_diff) < 0.1 and abs(angle_1) > 180.0:
                angle_diff = 360.0
            interpolator = _AxisAngleInterpolator(axis_x, axis_y, axis_z, angle_0, angle_diff, t0, t1)
    else:
        # 使用 SLERP 插值器
        interpolator = _SphericalLinearInterpolator(x0, y0, z0, w0, x1, y1, z1, w1, t0, t1)
    
    # 返回一个包装函数
    def slerp(t):
        return interpolator.evaluate(t)
    
    return slerp


# ==================== 欧拉角工具类和 SLERP 插值器 ====================

class _EulerSphericalLinearInterpolator:
    """
    欧拉角球面线性插值器
    
    提供欧拉角与四元数互转功能，以及在两个欧拉角之间进行 SLERP 的功能。
    支持轴角插值模式，用于处理 360° 等完整旋转。
    """

    def __init__(self, euler_x0: float, euler_y0: float, euler_z0: float,
                 euler_x1: float, euler_y1: float, euler_z1: float,
                 t0: float = 0.0, t1: float = 1.0, axis=None):
        
        # 保存起始和结束欧拉角
        self.euler_x0 = euler_x0
        self.euler_y0 = euler_y0
        self.euler_z0 = euler_z0
        self.euler_x1 = euler_x1
        self.euler_y1 = euler_y1
        self.euler_z1 = euler_z1
        self.t0 = t0
        self.t1 = t1
        
        # 解析轴方向
        self._axis_vec = None
        self._use_axis_angle = False
        
        if axis is not None:
            if isinstance(axis, str):
                axis_map = {'x': (1.0, 0.0, 0.0), 'y': (0.0, 1.0, 0.0), 'z': (0.0, 0.0, 1.0)}
                self._axis_vec = axis_map.get(axis.lower(), (0.0, 0.0, 1.0))
            else:
                self._axis_vec = tuple(float(v) for v in axis)
            self._use_axis_angle = True
        else:
            # 自动检测是否需要轴角插值
            self._use_axis_angle = self._detect_axis_angle_needed()
        
        if self._use_axis_angle:
            # 启用轴角插值模式
            if self._axis_vec is None:
                self._axis_vec = (0.0, 0.0, 1.0)  # 默认 Z 轴
            self._start_angle, self._total_angle = self._extract_axis_rotation()
        else:
            # 使用四元数 SLERP 模式
            # 处理角度差异，确保沿最短路径旋转
            adjusted_x1, adjusted_y1, adjusted_z1 = self._adjust_angles_for_shortest_path(
                euler_x0, euler_y0, euler_z0, euler_x1, euler_y1, euler_z1
            )
            
            # 将欧拉角转换为四元数并创建插值器
            quat_start = _euler_to_quaternion(euler_x0, euler_y0, euler_z0)
            quat_end = _euler_to_quaternion(adjusted_x1, adjusted_y1, adjusted_z1)
            
            # 检测四元数是否为完整旋转
            if _detect_full_rotation(*quat_start, *quat_end):
                # 切换到轴角插值
                self._use_axis_angle = True
                if self._axis_vec is None:
                    self._axis_vec = (0.0, 0.0, 1.0)  # 默认 Z 轴
                self._start_angle, self._total_angle = self._extract_axis_rotation()
            else:
                self._spherical_linear_interpolator = SphericalLinearInterpolation(
                    *quat_start, *quat_end, t0, t1
                )

    def _detect_axis_angle_needed(self) -> bool:
        """自动检测是否需要轴角插值"""
        diffs = [
            abs(self.euler_x1 - self.euler_x0),
            abs(self.euler_y1 - self.euler_y0),
            abs(self.euler_z1 - self.euler_z0)
        ]
        
        axes = [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)]
        
        for i, diff in enumerate(diffs):
            # 如果变化量大于 180° 且模 360° 接近 0
            if diff > 180.0 and abs(np.mod(diff, 360.0)) < 1.0:
                self._axis_vec = axes[i]
                return True
        
        return False

    def _extract_axis_rotation(self) -> tuple:
        """提取绕指定轴的起始角度和总旋转角度"""
        # 找到轴对应的索引
        if self._axis_vec[0] > 0.9:  # X轴
            idx = 0
        elif self._axis_vec[1] > 0.9:  # Y轴
            idx = 1
        else:  # Z轴
            idx = 2
        
        start_angles = [self.euler_x0, self.euler_y0, self.euler_z0]
        end_angles = [self.euler_x1, self.euler_y1, self.euler_z1]
        
        start_angle = start_angles[idx]
        total_angle = end_angles[idx] - start_angle
        
        # 确保总角度不为0（针对完整旋转）
        if abs(total_angle) < 0.01:
            total_angle = 360.0 if end_angles[idx] >= start_angles[idx] else -360.0
        
        return start_angle, total_angle

    def _adjust_angles_for_shortest_path(self, x0, y0, z0, x1, y1, z1):
        """
        调整目标角度以确保沿正确的路径旋转
        """
        # 计算每个轴的角度差并规范化到 [-180, 180]
        dx = _normalize_angle(x1 - x0)
        dy = _normalize_angle(y1 - y0)
        dz = _normalize_angle(z1 - z0)
        
        # 调整目标角度
        return x0 + dx, y0 + dy, z0 + dz

    def evaluate(self, t: float) -> tuple:
        """
        计算给定 t 值对应的插值欧拉角
        
        参数:
            t: 可以是归一化参数 [0, 1] 或实际时间值（如果设置了 t0, t1）
        
        返回:
            (euler_x, euler_y, euler_z) 欧拉角（度）
        """
        # 时间归一化
        if self.t1 != self.t0:
            t = (t - self.t0) / (self.t1 - self.t0)
            t = max(0.0, min(1.0, t))
        
        if self._use_axis_angle:
            # 轴角插值模式
            current_angle = self._start_angle + self._total_angle * t
            
            # 根据旋转轴组合欧拉角
            if self._axis_vec[0] > 0.9:  # 绕 X 轴
                quat = _euler_to_quaternion(current_angle, self.euler_y0, self.euler_z0)
            elif self._axis_vec[1] > 0.9:  # 绕 Y 轴
                quat = _euler_to_quaternion(self.euler_x0, current_angle, self.euler_z0)
            else:  # 绕 Z 轴
                quat = _euler_to_quaternion(self.euler_x0, self.euler_y0, current_angle)
            
            return _quaternion_to_euler(*quat)
        else:
            # SLERP 模式
            quat = self._spherical_linear_interpolator(t)
            return _quaternion_to_euler(*quat)

    @staticmethod
    def euler_to_quaternion(euler_x: float, euler_y: float, euler_z: float) -> tuple:
        """
        将欧拉角（度）转换为四元数
        
        旋转顺序：Z -> X -> Y (Unity 默认顺序)
        """
        return _euler_to_quaternion(euler_x, euler_y, euler_z)
    
    @staticmethod
    def quaternion_to_euler(x: float, y: float, z: float, w: float) -> tuple:
        """
        将四元数转换为欧拉角（度）
        
        返回顺序：X, Y, Z (Unity 默认顺序)
        """
        return _quaternion_to_euler(x, y, z, w)


def EulerSphericalLinearInterpolation(euler_x0: float, euler_y0: float, euler_z0: float,
                                      euler_x1: float, euler_y1: float, euler_z1: float,
                                      t0: float = 0.0, t1: float = 1.0, axis=None):
    """
    欧拉角球面线性插值器工厂函数
    
    在两个欧拉角之间进行球面线性插值。支持两种模式：
    1. SLERP 模式（默认）：通过四元数球面线性插值，适合一般旋转
    2. 轴角模式：绕固定轴匀速旋转，用于解决 360° 整圈旋转问题
    
    参数:
        euler_x0, euler_y0, euler_z0: 起始欧拉角（度）
        euler_x1, euler_y1, euler_z1: 结束欧拉角（度）
        t0, t1: 时间范围（可选），如果提供则自动进行时间归一化
        axis: 可选，指定绕哪个轴旋转。可以是 'x'/'y'/'z' 或三元组 (x, y, z)
              如果为 None，会自动检测是否需要轴角模式（某轴变化量 ≥ 360° 时）
    
    返回:
        一个可调用对象，接受 t 参数并返回插值后的欧拉角 (x, y, z)（度）
    
    示例:
        >>> # SLERP 模式（默认）
        >>> slerp = EulerSphericalLinearInterpolation(0, 0, 0, 90, 45, 0)
        >>> x, y, z = slerp(0.5)
        
        >>> # 轴角模式（手动指定绕 Z 轴旋转 360°）
        >>> slerp = EulerSphericalLinearInterpolation(0, 0, 0, 0, 0, 360, axis='z')
        >>> x, y, z = slerp(0.5)  # 结果约为 (0, 0, 180)
        
        >>> # 自动检测模式（自动启用轴角插值）
        >>> slerp = EulerSphericalLinearInterpolation(0, 0, 0, 0, 0, 360)
        >>> x, y, z = slerp(1.0)  # 完整旋转一圈
    """
    interpolator = _EulerSphericalLinearInterpolator(
        euler_x0, euler_y0, euler_z0,
        euler_x1, euler_y1, euler_z1,
        t0, t1, axis
    )
    
    def slerp(t):
        return interpolator.evaluate(t)
    
    return slerp