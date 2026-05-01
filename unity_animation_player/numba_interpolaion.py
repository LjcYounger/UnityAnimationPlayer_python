from .config import USE_JIT

if USE_JIT:
    try:
        from numba import njit
    except:
        njit = lambda *args, **kwargs: lambda f: f
else:
    njit = lambda *args, **kwargs: lambda f: f

from numba import njit
import numpy as np

@njit(cache=True)
def _hermite_spline_core(t, x0, x1, y0, y1, x1_ctl, y1_ctl, x2_ctl, y2_ctl, w0, w1, w2, w3):
    """核心计算逻辑，只编译一次"""
    # 解方程: (B0*w0*x0 + B1*w1*x1_ctl + B2*w2*x2_ctl + B3*w3*x1) / denom = t
    # 等价于: B0*w0*(x0-t) + B1*w1*(x1_ctl-t) + B2*w2*(x2_ctl-t) + B3*w3*(x1-t) = 0
    # 其中 B0=(1-u)^3, B1=3u(1-u)^2, B2=3u^2(1-u), B3=u^3
    
    # 整理成三次方程: a*u^3 + b*u^2 + c*u + d = 0
    a = w3*(x1-t) - 3*w2*(x2_ctl-t) + 3*w1*(x1_ctl-t) - w0*(x0-t)
    b = 3*w2*(x2_ctl-t) - 6*w1*(x1_ctl-t) + 3*w0*(x0-t)
    c = 3*w1*(x1_ctl-t) - 3*w0*(x0-t)
    d = w0*(x0-t)
    
    # 求三次方程在[0,1]内的实根
    # 使用卡丹公式或数值迭代，这里用牛顿法（3-5次即可）
    u = 0.5  # 初始猜测
    for _ in range(10):
        # 计算多项式值
        f = ((a * u + b) * u + c) * u + d
        f_prime = (3 * a * u + 2 * b) * u + c
        u_new = u - f / f_prime
        if abs(u_new - u) < 1e-12:
            u = u_new
            break
        u = u_new
    
    # 计算y坐标
    u1 = 1 - u
    B0 = u1 * u1 * u1
    B1 = 3 * u * u1 * u1
    B2 = 3 * u * u * u1
    B3 = u * u * u
    
    denom = B0*w0 + B1*w1 + B2*w2 + B3*w3
    y = (B0*w0*y0 + B1*w1*y1_ctl + B2*w2*y2_ctl + B3*w3*y1) / denom
    return y


def RationalBezierInterpolation(x0: float, x1: float, 
                       y0: float, y1: float, 
                       k0: float, k1: float, 
                       w0: float = 1.0, w1: float = 1.0, w2: float = 1.0, w3: float = 1.0):
    # 计算中间控制点（同之前）
    dx = x1 - x0
    dy = y1 - y0
    t_param = 1.0 / 3.0
    
    x1_ctl = x0 + t_param * dx
    y1_ctl = y0 + k0 * (x1_ctl - x0)
    
    x2_ctl = x0 + (1 - t_param) * dx
    y2_ctl = y1 - k1 * (x1 - x2_ctl)
    
    def spline(t):
        return _hermite_spline_core(t, x0, x1, y0, y1, x1_ctl, y1_ctl, x2_ctl, y2_ctl, w0, w1, w2, w3)
    
    return spline