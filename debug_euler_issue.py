from unity_animation_player import AnimationPlayer
import numpy as np

# 加载动画文件
player = AnimationPlayer("examples/AnimationClip/T.anim")

print("=" * 60)
print("Testing Euler angle interpolation:")
print("=" * 60)

# 手动测试欧拉角到四元数的转换
from unity_animation_player.numba_optimized.spherical_linear_interpolator import _EulerSphericalLinearInterpolator

# 起始和结束欧拉角（从 YAML 文件中）
euler_start = (0, 0, 0)
euler_end = (0, 0, 360)

print(f"\nStart Euler: {euler_start}")
print(f"End Euler: {euler_end}")

# 创建插值器
interp = _EulerSphericalLinearInterpolator(
    euler_start[0], euler_start[1], euler_start[2],
    euler_end[0], euler_end[1], euler_end[2],
    t0=0.0, t1=1.6333333
)

# 测试不同时间点
for t in [0.0, 0.5, 0.81666665, 1.0, 1.6333333]:
    result = interp.evaluate(t)
    print(f"At t={t:.2f}s: Euler = ({result[0]:.4f}, {result[1]:.4f}, {result[2]:.4f})")

# 检查四元数转换
print("\n" + "=" * 60)
print("Quaternion conversion check:")
print("=" * 60)

quat_start = interp.euler_to_quaternion(*euler_start)
quat_end = interp.euler_to_quaternion(*euler_end)

print(f"Start quaternion: ({quat_start[0]:.6f}, {quat_start[1]:.6f}, {quat_start[2]:.6f}, {quat_start[3]:.6f})")
print(f"End quaternion:   ({quat_end[0]:.6f}, {quat_end[1]:.6f}, {quat_end[2]:.6f}, {quat_end[3]:.6f})")

# 计算点积
dot = sum(a*b for a, b in zip(quat_start, quat_end))
print(f"Dot product: {dot:.6f}")
print(f"Angle between quaternions: {np.degrees(np.arccos(min(max(dot, -1), 1))):.2f} degrees")
