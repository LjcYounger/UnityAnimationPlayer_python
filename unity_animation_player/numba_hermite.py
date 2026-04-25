try:
    from numba import njit
except:
    njit = lambda *args, **kwargs: lambda f: f

def CubicHermiteSpline(x0: float, x1: float, y0: float, y1: float, d0: float, d1: float):
    
    @njit(cache=True)
    def spline(t):
        h = x1 - x0
        if h == 0:
            return y0
        
        t_norm = (t - x0) / h
        t2 = t_norm * t_norm
        t3 = t2 * t_norm
        
        return (2*t3 - 3*t2 + 1) * y0 + \
               (t3 - 2*t2 + t_norm) * d0 * h + \
               (-2*t3 + 3*t2) * y1 + \
               (t3 - t2) * d1 * h
    
    return spline