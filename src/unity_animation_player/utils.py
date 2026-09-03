import time
from functools import wraps

def timer(func):
    @wraps(func)  # Preserve the original function's metadata
    def wrapper(*args, **kwargs):
        start = time.perf_counter()  # Use a high-precision timer
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__} 耗时: {end - start:.4f} 秒")
        return result
    return wrapper