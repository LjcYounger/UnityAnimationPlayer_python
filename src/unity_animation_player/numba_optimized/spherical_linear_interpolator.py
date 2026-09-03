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


# ==================== Utility Functions ====================

@njit
def _clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value to the specified range."""
    if value < min_val:
        return min_val
    elif value > max_val:
        return max_val
    return value


@njit
def _axis_angle_to_quaternion(axis_x: float, axis_y: float, axis_z: float, angle_deg: float) -> tuple:
    """
    Convert an axis-angle (degrees) to a quaternion.

    Args:
        axis_x, axis_y, axis_z: The rotation axis vector.
        angle_deg: The rotation angle in degrees.

    Returns:
        The quaternion components (x, y, z, w).
    """
    half = np.radians(angle_deg) * 0.5
    s = np.sin(half)
    c = np.cos(half)
    
    # Normalize the axis vector
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
    Convert a quaternion to an axis-angle (degrees).

    Returns:
        (axis_x, axis_y, axis_z, angle_deg)
    """
    # Normalize
    length = np.sqrt(x*x + y*y + z*z + w*w)
    if length > 1e-15:
        x /= length
        y /= length
        z /= length
        w /= length
    
    # Clamp w to a valid range
    if w > 1.0:
        w = 1.0
    elif w < -1.0:
        w = -1.0
    
    angle_rad = 2.0 * np.arccos(w)
    angle_deg = np.degrees(angle_rad)
    
    sin_half = np.sin(angle_rad / 2.0)
    
    if abs(sin_half) < 1e-10:
        # Zero rotation, return the default axis
        return (1.0, 0.0, 0.0, 0.0)
    
    axis_x = x / sin_half
    axis_y = y / sin_half
    axis_z = z / sin_half
    
    return (axis_x, axis_y, axis_z, angle_deg)


@njit
def _euler_to_quaternion(euler_x: float, euler_y: float, euler_z: float) -> tuple:
    """
    Convert Euler angles (degrees) to a quaternion.

    Rotation order: Z -> X -> Y (Unity default order).

    Args:
        euler_x: X-axis rotation angle in degrees.
        euler_y: Y-axis rotation angle in degrees.
        euler_z: Z-axis rotation angle in degrees.

    Returns:
        The quaternion components (x, y, z, w).
    """
    # Convert the angles to radians and divide by 2
    cx = np.cos(np.radians(euler_x) * 0.5)
    sx = np.sin(np.radians(euler_x) * 0.5)
    cy = np.cos(np.radians(euler_y) * 0.5)
    sy = np.sin(np.radians(euler_y) * 0.5)
    cz = np.cos(np.radians(euler_z) * 0.5)
    sz = np.sin(np.radians(euler_z) * 0.5)
    
    # Quaternion formula for Unity's ZXY rotation order
    x = sx * cy * cz + cx * sy * sz
    y = cx * sy * cz - sx * cy * sz
    z = cx * cy * sz - sx * sy * cz
    w = cx * cy * cz + sx * sy * sz
    
    return (x, y, z, w)


@njit
def _quaternion_to_euler(x: float, y: float, z: float, w: float) -> tuple:
    """
    Convert a quaternion to Euler angles (degrees).

    Return order: X, Y, Z (Unity default order).

    Args:
        x, y, z, w: The four quaternion components.

    Returns:
        The Euler angles (euler_x, euler_y, euler_z) in degrees.
    """
    # Normalize the quaternion
    length = np.sqrt(x*x + y*y + z*z + w*w)
    if length > 1e-15:
        x /= length
        y /= length
        z /= length
        w /= length
    
    # Compute roll (x-axis rotation)
    sinr_cosp = 2.0 * (w * x + y * z)
    cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
    euler_x = np.degrees(np.arctan2(sinr_cosp, cosr_cosp))
    
    # Compute pitch (y-axis rotation)
    sinp = 2.0 * (w * y - z * x)
    if abs(sinp) >= 1.0:
        euler_y = np.degrees(np.copysign(np.pi / 2.0, sinp))
    else:
        euler_y = np.degrees(np.arcsin(sinp))
    
    # Compute yaw (z-axis rotation)
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    euler_z = np.degrees(np.arctan2(siny_cosp, cosy_cosp))
    
    return (euler_x, euler_y, euler_z)


@njit
def _normalize_angle(angle: float) -> float:
    """Normalize an angle to the range [-180, 180]."""
    return np.mod(angle + 180.0, 360.0) - 180.0


@njit
def _detect_full_rotation(x0: float, y0: float, z0: float, w0: float,
                          x1: float, y1: float, z1: float, w1: float) -> bool:
    """
    Detect whether two quaternions represent a full rotation (an integer multiple of 360 degrees).

    A full rotation is detected when the two quaternions describe the same orientation
    but have opposite signs, and the start quaternion is close to the identity transform.
    """
    # Compute the dot product
    dot = x0*x1 + y0*y1 + z0*z1 + w0*w1
    
    # If the dot product is close to -1, the two quaternions point in opposite directions
    if dot < -0.999:
        # Check whether the start quaternion is near the identity transform (0,0,0,1) or (0,0,0,-1)
        vec_len = x0*x0 + y0*y0 + z0*z0
        if vec_len < 0.001 * 0.001:  # The vector part is close to zero
            return True
    
    return False


# ==================== Quaternion SLERP Interpolator ====================

# Define the field type spec of the SLERP class
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

# Define the field type spec of the axis-angle interpolator
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
    Core spherical linear interpolator (Numba JIT compiled version).

    Performs spherical linear interpolation (SLERP) between two quaternions.
    This is an internal class; use the SphericalLinearInterpolation factory function externally.
    """
    
    def __init__(self, x0: float, y0: float, z0: float, w0: float,
                 x1: float, y1: float, z1: float, w1: float,
                 t0: float = 0.0, t1: float = 1.0):
        # Store the start and end quaternions
        self.x0 = x0
        self.y0 = y0
        self.z0 = z0
        self.w0 = w0
        self.x1 = x1
        self.y1 = y1
        self.z1 = z1
        self.w1 = w1
        # Store the time range to support automatic normalization
        self.t0 = t0
        self.t1 = t1
    
    def evaluate(self, t: float) -> tuple:
        """
        Compute the interpolated quaternion for the given t.

        Args:
            t: Either a normalized parameter in [0, 1] or an actual time value
               (if t0, t1 are set).

        Returns:
            The quaternion components (x, y, z, w).
        """
        # If a time range is set, normalize automatically
        if self.t1 != self.t0:
            t_normalized = (t - self.t0) / (self.t1 - self.t0)
            t_normalized = _clamp(t_normalized, 0.0, 1.0)
        else:
            t_normalized = t
        
        return self._slerp_core(t_normalized)
    
    def _slerp_core(self, t: float) -> tuple:
        """
        Core SLERP computation.

        Spherical linear interpolation formula:
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
        
        # Compute the dot product (cosine of the angle between the quaternions)
        dot = x0*x1 + y0*y1 + z0*z1 + w0*w1
        
        # If the dot product is negative, flip one quaternion to take the shortest path
        if dot < 0.0:
            x1 = -x1
            y1 = -y1
            z1 = -z1
            w1 = -w1
            dot = -dot
        
        # Clamp the dot product to prevent issues caused by numerical errors
        if dot > 1.0:
            dot = 1.0
        elif dot < -1.0:
            dot = -1.0
        
        # Compute the angle between the quaternions
        theta_0 = np.arccos(dot)
        sin_theta_0 = np.sin(theta_0)
        
        # If the angle is very small, use linear interpolation to avoid division by zero
        if abs(sin_theta_0) < 1e-6:
            # Linear interpolation
            x = x0 + t * (x1 - x0)
            y = y0 + t * (y1 - y0)
            z = z0 + t * (z1 - z0)
            w = w0 + t * (w1 - w0)
            
            # Normalize
            length = np.sqrt(x*x + y*y + z*z + w*w)
            if length > 1e-15:
                x /= length
                y /= length
                z /= length
                w /= length
            
            return (x, y, z, w)
        
        # Compute the interpolation coefficients
        sin_theta_t = np.sin(t * theta_0)
        sin_theta_1_t = np.sin((1.0 - t) * theta_0)
        
        s0 = sin_theta_1_t / sin_theta_0
        s1 = sin_theta_t / sin_theta_0
        
        # Compute the interpolated quaternion
        x = s0 * x0 + s1 * x1
        y = s0 * y0 + s1 * y1
        z = s0 * z0 + s1 * z1
        w = s0 * w0 + s1 * w1
        
        return (x, y, z, w)


@jitclass(spec_axis_angle)
class _AxisAngleInterpolator:
    """
    Axis-angle interpolator (Numba JIT compiled version).

    Interpolates the angle around a fixed axis, solving the problem where SLERP
    cannot handle a full 360-degree rotation. All fields must be predefined in the spec.
    """
    
    def __init__(self, axis_x: float, axis_y: float, axis_z: float, 
                 angle_start: float, angle_total: float,
                 t0: float = 0.0, t1: float = 1.0):
        # Store the axis vector
        self.axis_x = axis_x
        self.axis_y = axis_y
        self.axis_z = axis_z
        # Store the angle information
        self.angle_start = angle_start
        self.angle_total = angle_total
        # Store the time range
        self.t0 = t0
        self.t1 = t1
    
    def evaluate(self, t: float) -> tuple:
        """
        Compute the interpolated quaternion for the given t.

        Args:
            t: Either a normalized parameter in [0, 1] or an actual time value
               (if t0, t1 are set).

        Returns:
            The quaternion components (x, y, z, w).
        """
        # If a time range is set, normalize automatically
        if self.t1 != self.t0:
            t_normalized = (t - self.t0) / (self.t1 - self.t0)
            t_normalized = _clamp(t_normalized, 0.0, 1.0)
        else:
            t_normalized = t
        
        # Compute the current angle
        current_angle = self.angle_start + self.angle_total * t_normalized
        
        # Build the corresponding quaternion
        return _axis_angle_to_quaternion(self.axis_x, self.axis_y, self.axis_z, current_angle)


def SphericalLinearInterpolation(x0: float, y0: float, z0: float, w0: float,
                                 x1: float, y1: float, z1: float, w1: float,
                                 t0: float = 0.0, t1: float = 1.0, 
                                 force_axis_angle: bool = False):
    """
    Factory function for the spherical linear interpolator.

    Creates and returns a callable interpolator object used to interpolate between two quaternions.
    Uses SLERP by default, and automatically switches to axis-angle interpolation
    when a full rotation (360 degrees) is detected.

    Args:
        x0, y0, z0, w0: The four components of the start quaternion.
        x1, y1, z1, w1: The four components of the end quaternion.
        t0, t1: Optional time range. If provided, time is normalized automatically.
        force_axis_angle: Force axis-angle interpolation mode.

    Returns:
        A callable object that takes t and returns the interpolated quaternion (x, y, z, w).
        - If t0, t1 are provided: t can be an actual time value and is normalized automatically.
        - If t0, t1 are not provided: t should be a normalized parameter in [0, 1].

    Example:
        >>> # Regular SLERP interpolation
        >>> slerp = SphericalLinearInterpolation(0, 0, 0, 1, 0, 0, 0.7071, 0.7071)
        >>> x, y, z, w = slerp(0.5)
        
        >>> # Full 360-degree rotation (automatically switches to axis-angle mode)
        >>> slerp = SphericalLinearInterpolation(0, 0, 0, 1, 0, 0, 0, -1)
        >>> x, y, z, w = slerp(0.5)  # Rotates 180 degrees around the Z axis
    """
    # Detect whether axis-angle interpolation is needed
    use_axis_angle = force_axis_angle or _detect_full_rotation(x0, y0, z0, w0, x1, y1, z1, w1)
    
    if use_axis_angle:
        # Extract the axis-angle representation
        if abs(x0) < 0.001 and abs(y0) < 0.001 and abs(z0) < 0.001:
            # The start quaternion is near the identity transform; extract the axis from the end quaternion
            axis_x, axis_y, axis_z, angle_total = _quaternion_to_axis_angle(x1, y1, z1, w1)
            # If the angle is close to 360 degrees, keep the full rotation
            if abs(angle_total) < 0.1:
                angle_total = 360.0
            interpolator = _AxisAngleInterpolator(axis_x, axis_y, axis_z, 0.0, angle_total, t0, t1)
        else:
            # General case: extract the axis-angle representation
            axis_x, axis_y, axis_z, angle_0 = _quaternion_to_axis_angle(x0, y0, z0, w0)
            _, _, _, angle_1 = _quaternion_to_axis_angle(x1, y1, z1, w1)
            angle_diff = angle_1 - angle_0
            if abs(angle_diff) < 0.1 and abs(angle_1) > 180.0:
                angle_diff = 360.0
            interpolator = _AxisAngleInterpolator(axis_x, axis_y, axis_z, angle_0, angle_diff, t0, t1)
    else:
        # Use the SLERP interpolator
        interpolator = _SphericalLinearInterpolator(x0, y0, z0, w0, x1, y1, z1, w1, t0, t1)
    
    # Return a wrapper function
    def slerp(t):
        return interpolator.evaluate(t)
    
    return slerp


# ==================== Euler Angle Utilities and SLERP Interpolator ====================

class _EulerSphericalLinearInterpolator:
    """
    Euler angle spherical linear interpolator.

    Provides conversion between Euler angles and quaternions, as well as SLERP
    between two sets of Euler angles. Supports an axis-angle interpolation mode
    to handle full rotations such as 360 degrees.
    """

    def __init__(self, euler_x0: float, euler_y0: float, euler_z0: float,
                 euler_x1: float, euler_y1: float, euler_z1: float,
                 t0: float = 0.0, t1: float = 1.0, axis=None):
        
        # Store the start and end Euler angles
        self.euler_x0 = euler_x0
        self.euler_y0 = euler_y0
        self.euler_z0 = euler_z0
        self.euler_x1 = euler_x1
        self.euler_y1 = euler_y1
        self.euler_z1 = euler_z1
        self.t0 = t0
        self.t1 = t1
        
        # Resolve the axis direction
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
            # Automatically detect whether axis-angle interpolation is needed
            self._use_axis_angle = self._detect_axis_angle_needed()
        
        if self._use_axis_angle:
            # Enable axis-angle interpolation mode
            if self._axis_vec is None:
                self._axis_vec = (0.0, 0.0, 1.0)  # Default to the Z axis
            self._start_angle, self._total_angle = self._extract_axis_rotation()
        else:
            # Use the quaternion SLERP mode
            # Adjust the angle differences to ensure rotation along the shortest path
            adjusted_x1, adjusted_y1, adjusted_z1 = self._adjust_angles_for_shortest_path(
                euler_x0, euler_y0, euler_z0, euler_x1, euler_y1, euler_z1
            )
            
            # Convert the Euler angles to quaternions and create the interpolator
            quat_start = _euler_to_quaternion(euler_x0, euler_y0, euler_z0)
            quat_end = _euler_to_quaternion(adjusted_x1, adjusted_y1, adjusted_z1)
            
            # Detect whether the quaternions represent a full rotation
            if _detect_full_rotation(*quat_start, *quat_end):
                # Switch to axis-angle interpolation
                self._use_axis_angle = True
                if self._axis_vec is None:
                    self._axis_vec = (0.0, 0.0, 1.0)  # Default to the Z axis
                self._start_angle, self._total_angle = self._extract_axis_rotation()
            else:
                self._spherical_linear_interpolator = SphericalLinearInterpolation(
                    *quat_start, *quat_end, t0, t1
                )

    def _detect_axis_angle_needed(self) -> bool:
        """Automatically detect whether axis-angle interpolation is needed."""
        diffs = [
            abs(self.euler_x1 - self.euler_x0),
            abs(self.euler_y1 - self.euler_y0),
            abs(self.euler_z1 - self.euler_z0)
        ]
        
        axes = [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)]
        
        for i, diff in enumerate(diffs):
            # If the change exceeds 180 degrees and mod 360 is close to 0
            if diff > 180.0 and abs(np.mod(diff, 360.0)) < 1.0:
                self._axis_vec = axes[i]
                return True
        
        return False

    def _extract_axis_rotation(self) -> tuple:
        """Extract the start angle and the total rotation angle around the specified axis."""
        # Find the index corresponding to the axis
        if self._axis_vec[0] > 0.9:  # X axis
            idx = 0
        elif self._axis_vec[1] > 0.9:  # Y axis
            idx = 1
        else:  # Z axis
            idx = 2
        
        start_angles = [self.euler_x0, self.euler_y0, self.euler_z0]
        end_angles = [self.euler_x1, self.euler_y1, self.euler_z1]
        
        start_angle = start_angles[idx]
        total_angle = end_angles[idx] - start_angle
        
        # Ensure the total angle is not 0 (relevant for full rotations)
        if abs(total_angle) < 0.01:
            total_angle = 360.0 if end_angles[idx] >= start_angles[idx] else -360.0
        
        return start_angle, total_angle

    def _adjust_angles_for_shortest_path(self, x0, y0, z0, x1, y1, z1):
        """
        Adjust the target angles to ensure rotation along the correct path.
        """
        # Compute the per-axis angle differences and normalize them to [-180, 180]
        dx = _normalize_angle(x1 - x0)
        dy = _normalize_angle(y1 - y0)
        dz = _normalize_angle(z1 - z0)
        
        # Adjust the target angles
        return x0 + dx, y0 + dy, z0 + dz

    def evaluate(self, t: float) -> tuple:
        """
        Compute the interpolated Euler angles for the given t.

        Args:
            t: Either a normalized parameter in [0, 1] or an actual time value
               (if t0, t1 are set).

        Returns:
            The Euler angles (euler_x, euler_y, euler_z) in degrees.
        """
        # Time normalization
        if self.t1 != self.t0:
            t = (t - self.t0) / (self.t1 - self.t0)
            t = max(0.0, min(1.0, t))
        
        if self._use_axis_angle:
            # Axis-angle interpolation mode
            current_angle = self._start_angle + self._total_angle * t
            
            # Combine the Euler angles based on the rotation axis
            if self._axis_vec[0] > 0.9:  # Around the X axis
                quat = _euler_to_quaternion(current_angle, self.euler_y0, self.euler_z0)
            elif self._axis_vec[1] > 0.9:  # Around the Y axis
                quat = _euler_to_quaternion(self.euler_x0, current_angle, self.euler_z0)
            else:  # Around the Z axis
                quat = _euler_to_quaternion(self.euler_x0, self.euler_y0, current_angle)
            
            return _quaternion_to_euler(*quat)
        else:
            # SLERP mode
            quat = self._spherical_linear_interpolator(t)
            return _quaternion_to_euler(*quat)

    @staticmethod
    def euler_to_quaternion(euler_x: float, euler_y: float, euler_z: float) -> tuple:
        """
        Convert Euler angles (degrees) to a quaternion.

        Rotation order: Z -> X -> Y (Unity default order).
        """
        return _euler_to_quaternion(euler_x, euler_y, euler_z)
    
    @staticmethod
    def quaternion_to_euler(x: float, y: float, z: float, w: float) -> tuple:
        """
        Convert a quaternion to Euler angles (degrees).

        Return order: X, Y, Z (Unity default order).
        """
        return _quaternion_to_euler(x, y, z, w)


def EulerSphericalLinearInterpolation(euler_x0: float, euler_y0: float, euler_z0: float,
                                      euler_x1: float, euler_y1: float, euler_z1: float,
                                      t0: float = 0.0, t1: float = 1.0, axis=None):
    """
    Factory function for the Euler angle spherical linear interpolator.

    Performs spherical linear interpolation between two sets of Euler angles. Supports two modes:
    1. SLERP mode (default): interpolates through quaternions, suitable for general rotations.
    2. Axis-angle mode: rotates uniformly around a fixed axis, used to solve full 360-degree rotations.

    Args:
        euler_x0, euler_y0, euler_z0: The start Euler angles (degrees).
        euler_x1, euler_y1, euler_z1: The end Euler angles (degrees).
        t0, t1: Optional time range. If provided, time is normalized automatically.
        axis: Optional. Specifies the axis of rotation. Can be 'x'/'y'/'z' or a tuple (x, y, z).
              If None, automatically detects whether axis-angle mode is needed
              (when the change on some axis is >= 360 degrees).

    Returns:
        A callable object that takes t and returns the interpolated Euler angles (x, y, z) in degrees.

    Example:
        >>> # SLERP mode (default)
        >>> slerp = EulerSphericalLinearInterpolation(0, 0, 0, 90, 45, 0)
        >>> x, y, z = slerp(0.5)
        
        >>> # Axis-angle mode (manually rotate 360 degrees around the Z axis)
        >>> slerp = EulerSphericalLinearInterpolation(0, 0, 0, 0, 0, 360, axis='z')
        >>> x, y, z = slerp(0.5)  # Result is approximately (0, 0, 180)
        
        >>> # Auto-detection mode (axis-angle interpolation enabled automatically)
        >>> slerp = EulerSphericalLinearInterpolation(0, 0, 0, 0, 0, 360)
        >>> x, y, z = slerp(1.0)  # Full rotation
    """
    interpolator = _EulerSphericalLinearInterpolator(
        euler_x0, euler_y0, euler_z0,
        euler_x1, euler_y1, euler_z1,
        t0, t1, axis
    )
    
    def slerp(t):
        return interpolator.evaluate(t)
    
    return slerp