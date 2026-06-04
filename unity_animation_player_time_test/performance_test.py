"""
性能测试示例脚本
展示如何使用计时装饰器和上下文管理器
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unity_animation_player_time_test.utils import timer, timer_context, ENABLE_PROFILING
from unity_animation_player_time_test.animation_player import AnimationPlayer

# 启用性能分析
ENABLE_PROFILING = True

def test_basic_timer():
    """测试基本计时器功能"""
    print("=" * 60)
    print("测试1: 基本计时器装饰器")
    print("=" * 60)
    
    @timer
    def sample_function():
        import time
        time.sleep(0.1)
        return "完成"
    
    result = sample_function()
    print(f"函数返回: {result}\n")


def test_custom_name_timer():
    """测试自定义名称的计时器"""
    print("=" * 60)
    print("测试2: 自定义名称计时器")
    print("=" * 60)
    
    @timer(name="自定义任务")
    def custom_task():
        import time
        time.sleep(0.05)
        return "自定义任务完成"
    
    result = custom_task()
    print(f"函数返回: {result}\n")


def test_threshold_timer():
    """测试带阈值的计时器（只显示超过阈值的调用）"""
    print("=" * 60)
    print("测试3: 带阈值的计时器（阈值=0.08秒）")
    print("=" * 60)
    
    @timer(log_threshold=0.08)
    def fast_operation():
        import time
        time.sleep(0.05)  # 低于阈值，不会打印
    
    @timer(log_threshold=0.08)
    def slow_operation():
        import time
        time.sleep(0.1)  # 高于阈值，会打印
    
    print("执行快速操作（不应显示日志）:")
    fast_operation()
    
    print("执行慢速操作（应显示日志）:")
    slow_operation()
    print()


def test_context_manager():
    """测试上下文管理器形式的计时器"""
    print("=" * 60)
    print("测试4: 上下文管理器计时器")
    print("=" * 60)
    
    with timer_context("代码块1"):
        import time
        time.sleep(0.05)
        print("代码块1执行中...")
    
    with timer_context("代码块2", log_threshold=0.08):
        time.sleep(0.1)
        print("代码块2执行中...")
    print()


def test_animation_player_performance():
    """测试动画播放器的性能"""
    print("=" * 60)
    print("测试5: 动画播放器性能测试")
    print("=" * 60)
    
    # 注意：这里需要一个实际的动画文件路径
    # 如果没有可用文件，这个测试会跳过
    test_file = "test_anim.anim"
    
    if os.path.exists(test_file):
        print(f"加载动画文件: {test_file}")
        player = AnimationPlayer(test_file)
        
        # 测试 play_frame 的性能
        print("\n测试 play_frame 方法（采样10帧）:")
        for i in range(10):
            t = i * 0.1
            result, playable = player.play_frame(t, path='general')
        
        print(f"\n动画总时长: {player.stop_time} 秒")
    else:
        print(f"跳过测试：找不到测试文件 '{test_file}'")
        print("提示：请提供一个有效的 .anim 文件进行性能测试\n")


def test_disable_profiling():
    """测试禁用性能分析"""
    print("=" * 60)
    print("测试6: 禁用性能分析")
    print("=" * 60)
    
    global ENABLE_PROFILING
    ENABLE_PROFILING = False
    
    @timer
    def silent_function():
        import time
        time.sleep(0.05)
        return "静默执行"
    
    print("执行函数（不应显示任何性能日志）:")
    result = silent_function()
    print(f"函数返回: {result}")
    
    # 重新启用
    ENABLE_PROFILING = True
    print("\n性能分析已重新启用\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Unity Animation Player - 性能测试套件")
    print("=" * 60 + "\n")
    
    test_basic_timer()
    test_custom_name_timer()
    test_threshold_timer()
    test_context_manager()
    test_animation_player_performance()
    test_disable_profiling()
    
    print("=" * 60)
    print("所有测试完成！")
    print("=" * 60)
