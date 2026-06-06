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
    使用 np.searchsorted 找到时间点 t 应该使用的曲线段索引
    
    参数:
        time_nodes: 时间节点数组，形状为 (n,)，已排序的时间点
        t: 当前查询的时间点
    
    返回:
        应该使用的曲线段索引（0 到 len(time_nodes)-2）
        如果 t 小于第一个时间点，返回 0
        如果 t 大于最后一个时间点，返回 len(time_nodes)-2
    
    说明:
        - time_nodes 有 n 个时间点，对应 n-1 个曲线段
        - 第 i 个曲线段覆盖 [time_nodes[i], time_nodes[i+1]] 区间
        - 返回值 i 表示应该使用第 i 个曲线段进行插值
    
    示例:
        >>> time_nodes = np.array([0.0, 0.5, 1.0, 1.5])
        >>> binary_search_segment_index(time_nodes, 0.3)  # 返回 0
        >>> binary_search_segment_index(time_nodes, 0.7)  # 返回 1
        >>> binary_search_segment_index(time_nodes, 1.2)  # 返回 2
    """
    n = len(time_nodes)
    
    # 边界情况检查
    if n < 2:
        return 0
    
    # 使用 np.searchsorted 找到插入位置
    # searchsorted 返回的是使得数组保持有序的插入位置
    # side='right' 确保当 t 等于某个时间点时，返回该时间点的下一个位置
    idx = np.searchsorted(time_nodes, t, side='right') - 1
    
    # 确保索引在有效范围内 [0, n-2]
    # idx 的范围是 [-1, n-1]，需要调整到 [0, n-2]
    if idx < 0:
        return 0
    elif idx >= n - 1:
        return n - 2
    else:
        return idx