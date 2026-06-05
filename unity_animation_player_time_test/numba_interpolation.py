from .config import USE_JIT
from .utils import timer

if USE_JIT:
    try:
        from numba import njit
    except:
        njit = lambda *args, **kwargs: lambda f: f
else:
    njit = lambda *args, **kwargs: lambda f: f


@njit(cache=True)
def _hermite_spline_core(t, x0, x1, y0, y1, x1_ctl, y1_ctl, x2_ctl, y2_ctl, w0, w1, w2, w3):
    a = w3*(x1-t) - 3*w2*(x2_ctl-t) + 3*w1*(x1_ctl-t) - w0*(x0-t)
    b = 3*w2*(x2_ctl-t) - 6*w1*(x1_ctl-t) + 3*w0*(x0-t)
    c = 3*w1*(x1_ctl-t) - 3*w0*(x0-t)
    d = w0*(x0-t)
    
    # 牛顿法
    u = 0.5
    for _ in range(10):
        f = ((a * u + b) * u + c) * u + d
        f_prime = (3 * a * u + 2 * b) * u + c
        u_new = u - f / f_prime
        if abs(u_new - u) < 1e-12:
            u = u_new
            break
        u = u_new
    
    u1 = 1 - u
    B0 = u1 * u1 * u1
    B1 = 3 * u * u1 * u1
    B2 = 3 * u * u * u1
    B3 = u * u * u
    
    denom = B0*w0 + B1*w1 + B2*w2 + B3*w3
    y = (B0*w0*y0 + B1*w1*y1_ctl + B2*w2*y2_ctl + B3*w3*y1) / denom
    return y


@timer(name="RationalBezierInterpolation")
def RationalBezierInterpolation(x0: float, x1: float, 
                       y0: float, y1: float, 
                       k0: float, k1: float, 
                       w0: float = 1.0, w1: float = 1.0, w2: float = 1.0, w3: float = 1.0):

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