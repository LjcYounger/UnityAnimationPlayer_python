import numpy as np
from ..config import USE_JIT

if USE_JIT:
    try:
        from numba import njit, float64, int64
    except ImportError:
        njit = lambda *args, **kwargs: lambda f: f
else:
    njit = lambda *args, **kwargs: lambda f: f


@njit(cache=True)
def binary_search_segment_index(time_nodes: np.array, t: float) -> int:
    """
    Use np.searchsorted to find the curve segment index for time point t.

    Args:
        time_nodes: Array of time nodes, shape (n,), sorted time points.
        t: The current time point to query.

    Returns:
        The curve segment index to use (0 to len(time_nodes)-2).
        Returns 0 if t is less than the first time point.
        Returns len(time_nodes)-2 if t is greater than the last time point.

    Notes:
        - time_nodes has n time points, corresponding to n-1 curve segments.
        - The i-th curve segment covers the interval [time_nodes[i], time_nodes[i+1]].
        - The returned index i indicates that the i-th curve segment should be used for interpolation.

    Example:
        >>> time_nodes = np.array([0.0, 0.5, 1.0, 1.5])
        >>> binary_search_segment_index(time_nodes, 0.3)  # returns 0
        >>> binary_search_segment_index(time_nodes, 0.7)  # returns 1
        >>> binary_search_segment_index(time_nodes, 1.2)  # returns 2
    """
    n = len(time_nodes)
    
    # Check for edge cases
    if n < 2:
        return 0
    
    # Use np.searchsorted to find the insertion position
    # searchsorted returns the insertion position that keeps the array sorted
    # side='right' ensures that when t equals a time point, the next position is returned
    idx = np.searchsorted(time_nodes, t, side='right') - 1
    
    # Ensure the index is within the valid range [0, n-2]
    # idx ranges over [-1, n-1] and needs to be clamped to [0, n-2]
    if idx < 0:
        return 0
    elif idx >= n - 1:
        return n - 2
    else:
        return idx