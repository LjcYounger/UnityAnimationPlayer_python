import time
from functools import wraps

def timer(func):
    @wraps(func)  # 保留原函数的元数据
    def wrapper(*args, **kwargs):
        start = time.perf_counter()  # 使用高精度计时器
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__} 耗时: {end - start:.4f} 秒")
        return result
    return wrapper