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


# 定义类的字段类型规范
spec = [
    ('x0', float64),
    ('x1', float64),
    ('y0', float64),
    ('y1', float64),
    ('x1_ctl', float64),
    ('y1_ctl', float64),
    ('x2_ctl', float64),
    ('y2_ctl', float64),
    ('w0', float64),
    ('w1', float64),
    ('w2', float64),
    ('w3', float64),
]


@jitclass(spec)
class _RationalBezierInterpolator:
    """
    有理贝塞尔插值器核心（Numba JIT 编译版本）
    
    通过预计算控制点参数，避免每次调用都重新计算。
    这是一个内部类，外部使用 RationalBezierInterpolation 工厂函数
    """
    
    def __init__(self, x0: float, x1: float, 
                 y0: float, y1: float, 
                 k0: float, k1: float, 
                 w0: float = 1.0, w1: float = 1.0, w2: float = 1.0, w3: float = 1.0):
        # 保存端点和权重
        self.x0 = x0
        self.x1 = x1
        self.y0 = y0
        self.y1 = y1
        self.w0 = w0
        self.w1 = w1
        self.w2 = w2
        self.w3 = w3
        
        # 预计算控制点
        dx = x1 - x0
        t_param = 1.0 / 3.0
        
        self.x1_ctl = x0 + t_param * dx
        self.y1_ctl = y0 + k0 * (self.x1_ctl - x0)
        
        self.x2_ctl = x0 + (1.0 - t_param) * dx
        self.y2_ctl = y1 - k1 * (x1 - self.x2_ctl)
    
    def evaluate(self, t: float) -> float:
        """
        计算给定 t 值对应的 y 值
        
        参数:
            t: 时间参数，范围通常在 [x0, x1]
        
        返回:
            插值后的 y 值
        """
        return self._hermite_spline_core(t)
    
    def _hermite_spline_core(self, t: float) -> float:
        """
        Hermite 样条核心计算（牛顿法求解）
        """
        x0 = self.x0
        x1 = self.x1
        y0 = self.y0
        y1 = self.y1
        x1_ctl = self.x1_ctl
        y1_ctl = self.y1_ctl
        x2_ctl = self.x2_ctl
        y2_ctl = self.y2_ctl
        w0 = self.w0
        w1 = self.w1
        w2 = self.w2
        w3 = self.w3
        
        # 构造三次方程系数
        a = w3*(x1-t) - 3*w2*(x2_ctl-t) + 3*w1*(x1_ctl-t) - w0*(x0-t)
        b = 3*w2*(x2_ctl-t) - 6*w1*(x1_ctl-t) + 3*w0*(x0-t)
        c = 3*w1*(x1_ctl-t) - 3*w0*(x0-t)
        d = w0*(x0-t)
        
        # 牛顿法求解 u
        u = 0.5
        for _ in range(10):
            f = ((a * u + b) * u + c) * u + d
            f_prime = (3 * a * u + 2 * b) * u + c
            if abs(f_prime) < 1e-15:  # 防止除零
                break
            u_new = u - f / f_prime
            if abs(u_new - u) < 1e-12:
                u = u_new
                break
            u = u_new
        
        # 计算伯恩斯坦多项式
        u1 = 1.0 - u
        B0 = u1 * u1 * u1
        B1 = 3.0 * u * u1 * u1
        B2 = 3.0 * u * u * u1
        B3 = u * u * u
        
        # 计算加权分母和分子
        denom = B0*w0 + B1*w1 + B2*w2 + B3*w3
        
        if abs(denom) < 1e-15:  # 防止除零
            return y0
        
        y = (B0*w0*y0 + B1*w1*y1_ctl + B2*w2*y2_ctl + B3*w3*y1) / denom
        return y


def RationalBezierInterpolation(x0: float, x1: float, 
                       y0: float, y1: float, 
                       k0: float, k1: float, 
                       w0: float = 1.0, w1: float = 1.0, w2: float = 1.0, w3: float = 1.0):
    """
    有理贝塞尔插值器工厂函数
    
    创建并返回一个可调用的插值器对象。
    内部使用 Numba JIT 编译的类来实现高性能计算。
    
    参数:
        x0, x1: 起始和结束的时间值
        y0, y1: 起始和结束的数值
        k0, k1: 起始和结束的斜率
        w0, w1, w2, w3: 权重参数（默认为 1.0）
    
    返回:
        一个可调用对象，接受 t 参数并返回插值后的 y 值
    
    示例:
        >>> interp = RationalBezierInterpolation(0, 1, 0, 1, 0, 0)
        >>> y = interp(0.5)  # 计算 t=0.5 时的值
    """
    # 创建 JIT 编译的插值器实例
    interpolator = _RationalBezierInterpolator(x0, x1, y0, y1, k0, k1, w0, w1, w2, w3)
    
    # 返回一个包装函数，使其可以像普通函数一样被调用
    def spline(t):
        return interpolator.evaluate(t)
    
    return spline
