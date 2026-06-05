import time
from functools import wraps
from typing import Callable, Optional

# 全局配置：是否启用性能计时
ENABLE_PROFILING = True

def timer(func: Optional[Callable] = None, *, name: Optional[str] = None, log_threshold: float = 0.0):
    """
    性能计时装饰器
    
    Args:
        func: 被装饰的函数
        name: 自定义显示名称（默认使用函数名）
        log_threshold: 日志阈值（秒），只有超过此阈值的调用才会打印日志（0表示全部打印）
    
    Usage:
        @timer
        def my_func(): ...
        
        @timer(name="Custom Name")
        def my_func(): ...
        
        @timer(log_threshold=0.01)  # 只记录超过10ms的调用
        def my_func(): ...
    """
    def decorator(fn: Callable) -> Callable:
        display_name = name or fn.__qualname__
        
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not ENABLE_PROFILING:
                return fn(*args, **kwargs)
            
            start = time.perf_counter()
            try:
                result = fn(*args, **kwargs)
                return result
            finally:
                end = time.perf_counter()
                elapsed = end - start
                if elapsed >= log_threshold:
                    print(f"[PERF] {display_name} 耗时: {elapsed:.6f} 秒")
        
        return wrapper
    
    # 支持无参数调用 @timer
    if func is not None:
        return decorator(func)
    return decorator


def timer_context(name: str, log_threshold: float = 0.0):
    """
    上下文管理器形式的计时器，用于代码块计时
    
    Usage:
        with timer_context("My Code Block"):
            # some code here
            pass
    """
    class TimerContext:
        def __init__(self, block_name: str, threshold: float):
            self.block_name = block_name
            self.threshold = threshold
            self.start_time = None
        
        def __enter__(self):
            if ENABLE_PROFILING:
                self.start_time = time.perf_counter()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            if ENABLE_PROFILING and self.start_time is not None:
                end = time.perf_counter()
                elapsed = end - self.start_time
                if elapsed >= self.threshold:
                    print(f"[PERF] {self.block_name} 耗时: {elapsed:.6f} 秒")
            return False
    
    return TimerContext(name, log_threshold)
