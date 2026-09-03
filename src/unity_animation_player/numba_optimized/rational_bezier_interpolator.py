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


# Define the field type spec of the class
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
    Core rational Bezier interpolator (Numba JIT compiled version).

    Precomputes the control point parameters so they are not recomputed on every call.
    This is an internal class; use the RationalBezierInterpolation factory function externally.
    """
    
    def __init__(self, x0: float, x1: float, 
                 y0: float, y1: float, 
                 k0: float, k1: float, 
                 w0: float = 1.0, w1: float = 1.0, w2: float = 1.0, w3: float = 1.0):
        # Store the endpoints and weights
        self.x0 = x0
        self.x1 = x1
        self.y0 = y0
        self.y1 = y1
        self.w0 = w0
        self.w1 = w1
        self.w2 = w2
        self.w3 = w3
        
        # Precompute the control points
        dx = x1 - x0
        t_param = 1.0 / 3.0
        
        self.x1_ctl = x0 + t_param * dx
        self.y1_ctl = y0 + k0 * (self.x1_ctl - x0)
        
        self.x2_ctl = x0 + (1.0 - t_param) * dx
        self.y2_ctl = y1 - k1 * (x1 - self.x2_ctl)
    
    def evaluate(self, t: float) -> float:
        """
        Compute the y value corresponding to the given t.

        Args:
            t: Time parameter, typically in the range [x0, x1].

        Returns:
            The interpolated y value.
        """
        return self._hermite_spline_core(t)
    
    def _hermite_spline_core(self, t: float) -> float:
        """
        Core Hermite spline computation (solved with Newton's method).
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
        
        # Build the cubic equation coefficients
        a = w3*(x1-t) - 3*w2*(x2_ctl-t) + 3*w1*(x1_ctl-t) - w0*(x0-t)
        b = 3*w2*(x2_ctl-t) - 6*w1*(x1_ctl-t) + 3*w0*(x0-t)
        c = 3*w1*(x1_ctl-t) - 3*w0*(x0-t)
        d = w0*(x0-t)
        
        # Solve for u using Newton's method
        u = 0.5
        for _ in range(10):
            f = ((a * u + b) * u + c) * u + d
            f_prime = (3 * a * u + 2 * b) * u + c
            if abs(f_prime) < 1e-15:  # Prevent division by zero
                break
            u_new = u - f / f_prime
            if abs(u_new - u) < 1e-12:
                u = u_new
                break
            u = u_new
        
        # Compute the Bernstein polynomials
        u1 = 1.0 - u
        B0 = u1 * u1 * u1
        B1 = 3.0 * u * u1 * u1
        B2 = 3.0 * u * u * u1
        B3 = u * u * u
        
        # Compute the weighted denominator and numerator
        denom = B0*w0 + B1*w1 + B2*w2 + B3*w3
        
        if abs(denom) < 1e-15:  # Prevent division by zero
            return y0
        
        y = (B0*w0*y0 + B1*w1*y1_ctl + B2*w2*y2_ctl + B3*w3*y1) / denom
        return y


def RationalBezierInterpolation(x0: float, x1: float, 
                       y0: float, y1: float, 
                       k0: float, k1: float, 
                       w0: float = 1.0, w1: float = 1.0, w2: float = 1.0, w3: float = 1.0):
    """
    Factory function for the rational Bezier interpolator.

    Creates and returns a callable interpolator object.
    Internally uses a Numba JIT compiled class for high-performance computation.

    Args:
        x0, x1: Start and end time values.
        y0, y1: Start and end values.
        k0, k1: Start and end slopes.
        w0, w1, w2, w3: Weight parameters (default to 1.0).

    Returns:
        A callable object that takes t and returns the interpolated y value.

    Example:
        >>> interp = RationalBezierInterpolation(0, 1, 0, 1, 0, 0)
        >>> y = interp(0.5)  # Compute the value at t=0.5
    """
    # Create a JIT compiled interpolator instance
    interpolator = _RationalBezierInterpolator(x0, x1, y0, y1, k0, k1, w0, w1, w2, w3)
    
    # Return a wrapper function so it can be called like a regular function
    def spline(t):
        return interpolator.evaluate(t)
    
    return spline
