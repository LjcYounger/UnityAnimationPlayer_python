from ..config import USE_JIT
import numpy as np

if USE_JIT:
    try:
        from numba import njit, float64
        from numba.experimental import jitclass
    except:
        njit = lambda *args, **kwargs: lambda f: f
        jitclass = lambda spec: lambda cls: cls
        float64 = float
else:
    njit = lambda *args, **kwargs: lambda f: f
    jitclass = lambda spec: lambda cls: cls
    float64 = float


# ==================== 四元数 SLERP 插值器 ====================

# 定义类的字段类型规范
spec_quaternion = [
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


@jitclass(spec_quaternion)
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
            # 限制在 [0, 1] 范围内
            if t_normalized < 0.0:
                t_normalized = 0.0
            elif t_normalized > 1.0:
                t_normalized = 1.0
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


def SphericalLinearInterpolation(x0: float, y0: float, z0: float, w0: float,
                                 x1: float, y1: float, z1: float, w1: float,
                                 t0: float = 0.0, t1: float = 1.0):
    """
    球面线性插值器工厂函数
    
    创建并返回一个可调用的插值器对象，用于在两个四元数之间进行 SLERP。
    内部使用 Numba JIT 编译的类来实现高性能计算。
    
    参数:
        x0, y0, z0, w0: 起始四元数的四个分量
        x1, y1, z1, w1: 结束四元数的四个分量
        t0, t1: 时间范围（可选），如果提供则自动进行时间归一化
    
    返回:
        一个可调用对象，接受 t 参数并返回插值后的四元数 (x, y, z, w)
        - 如果提供了 t0, t1：t 可以是实际时间值，会自动归一化
        - 如果未提供 t0, t1：t 应该是归一化参数 [0, 1]
    
    示例:
        >>> # 使用归一化时间
        >>> slerp = SphericalLinearInterpolation(0, 0, 0, 1, 0, 0, 0.7071, 0.7071)
        >>> x, y, z, w = slerp(0.5)  # t=0.5 (已归一化)
        
        >>> # 使用实际时间
        >>> slerp = SphericalLinearInterpolation(0, 0, 0, 1, 0, 0, 0.7071, 0.7071, t0=0.0, t1=2.0)
        >>> x, y, z, w = slerp(1.0)  # t=1.0 (实际时间，自动归一化为 0.5)
    """
    # 创建 JIT 编译的插值器实例
    interpolator = _SphericalLinearInterpolator(x0, y0, z0, w0, x1, y1, z1, w1, t0, t1)
    
    # 返回一个包装函数，使其可以像普通函数一样被调用
    def slerp(t):
        return interpolator.evaluate(t)
    
    return slerp


# ==================== 欧拉角工具类和 SLERP 插值器 ====================

class _EulerSphericalLinearInterpolator:
    """
    欧拉角球面线性插值器
    
    提供欧拉角与四元数互转功能，以及在两个欧拉角之间进行 SLERP 的功能。
    内部使用 _SphericalLinearInterpolator 进行四元数插值。
    """

    def __init__(self, euler_x0: float, euler_y0: float, euler_z0: float,
                    euler_x1: float, euler_y1: float, euler_z1: float,
                    t0: float = 0.0, t1: float = 1.0):
        # 保存起始和结束欧拉角
        self.euler_x0 = euler_x0
        self.euler_y0 = euler_y0
        self.euler_z0 = euler_z0
        self.euler_x1 = euler_x1
        self.euler_y1 = euler_y1
        self.euler_z1 = euler_z1

        # 将欧拉角转换为四元数并创建 SLERP 插值器（带时间范围）
        quat_start = self.euler_to_quaternion(self.euler_x0, self.euler_y0, self.euler_z0)
        quat_end = self.euler_to_quaternion(self.euler_x1, self.euler_y1, self.euler_z1)
        self._spherical_linear_interpolator = _SphericalLinearInterpolator(
            *quat_start, *quat_end, t0, t1
        )

    def evaluate(self, t: float) -> tuple:
        """
        计算给定 t 值对应的插值欧拉角
        
        参数:
            t: 可以是归一化参数 [0, 1] 或实际时间值（如果设置了 t0, t1）
        
        返回:
            (euler_x, euler_y, euler_z) 欧拉角（度）
        """
        # 直接使用内部插值器的 evaluate，它会自动处理时间归一化
        return self.quaternion_to_euler(*self._spherical_linear_interpolator.evaluate(t))


    @staticmethod
    def euler_to_quaternion(euler_x: float, euler_y: float, euler_z: float) -> tuple:
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
        # 规范化欧拉角到 [-180, 180] 范围，避免 360 度等问题
        euler_x = np.mod(euler_x + 180.0, 360.0) - 180.0
        euler_y = np.mod(euler_y + 180.0, 360.0) - 180.0
        euler_z = np.mod(euler_z + 180.0, 360.0) - 180.0
        
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
    
    @staticmethod
    def quaternion_to_euler(x: float, y: float, z: float, w: float) -> tuple:
        """
        将四元数转换为欧拉角（度）
        
        返回顺序：X, Y, Z (Unity 默认顺序)
        
        参数:
            x, y, z, w: 四元数的四个分量
        
        返回:
            (euler_x, euler_y, euler_z) 欧拉角（度）
        """
        # 计算 roll (x-axis rotation)
        sinr_cosp = 2.0 * (w * x + y * z)
        cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
        euler_x = np.degrees(np.arctan2(sinr_cosp, cosr_cosp))
        
        # 计算 pitch (y-axis rotation)
        sinp = 2.0 * (w * y - z * x)
        if abs(sinp) >= 1.0:
            euler_y = np.degrees(np.copysign(np.pi / 2.0, sinp))  # 使用90度如果超出范围
        else:
            euler_y = np.degrees(np.arcsin(sinp))
        
        # 计算 yaw (z-axis rotation)
        siny_cosp = 2.0 * (w * z + x * y)
        cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
        euler_z = np.degrees(np.arctan2(siny_cosp, cosy_cosp))
        
        return (euler_x, euler_y, euler_z)


def EulerSphericalLinearInterpolation(euler_x0: float, euler_y0: float, euler_z0: float,
                    euler_x1: float, euler_y1: float, euler_z1: float,
                    t0: float = 0.0, t1: float = 1.0):
    """
    欧拉角球面线性插值器工厂函数
    
    在两个欧拉角之间进行球面线性插值。内部先将欧拉角转换为四元数，
    然后使用 SLERP 进行插值，最后将结果转换回欧拉角。
    这种方法可以避免万向节锁问题并提供更平滑的旋转插值。
    
    参数:
        euler_x0, euler_y0, euler_z0: 起始欧拉角（度）
        euler_x1, euler_y1, euler_z1: 结束欧拉角（度）
        t0, t1: 时间范围（可选），如果提供则自动进行时间归一化
    
    返回:
        一个可调用对象，接受 t 参数并返回插值后的欧拉角 (x, y, z)（度）
        - 如果提供了 t0, t1：t 可以是实际时间值，会自动归一化
        - 如果未提供 t0, t1：t 应该是归一化参数 [0, 1]
    
    示例:
        >>> # 使用归一化时间
        >>> slerp = EulerSphericalLinearInterpolation(0, 0, 0, 90, 45, 0)
        >>> x, y, z = slerp(0.5)  # t=0.5 (已归一化)
        
        >>> # 使用实际时间
        >>> slerp = EulerSphericalLinearInterpolation(0, 0, 0, 90, 45, 0, t0=0.0, t1=2.0)
        >>> x, y, z = slerp(1.0)  # t=1.0 (实际时间，自动归一化为 0.5)
    """
    interpolator = _EulerSphericalLinearInterpolator(euler_x0, euler_y0, euler_z0, euler_x1, euler_y1, euler_z1, t0, t1)
    
    # 返回一个包装函数，直接计算避免闭包开销
    def slerp(t):
        return interpolator.evaluate(t)
    
    return slerp
