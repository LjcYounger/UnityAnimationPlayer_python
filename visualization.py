
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

# Import your original AnimationPlayer without modification
from animation_player import AnimationPlayer


def main():
    # 1. Input animation file path
    #anim_path = input("Enter animation file path (e.g., examples/AnimationClip/UIAni_SC_Char_Shake_3.anim): ").strip()
    anim_path = "examples/AnimationClip/T.anim"
    
    try:
        player = AnimationPlayer(anim_path)
    except Exception as e:
        print(f"❌ Failed to load animation: {e}")
        return

    # 2. Get all available paths (animation segments)
    all_paths = list(player.anim.keys())
    if not all_paths:
        print("⚠️ No animation paths found in the file.")
        return

    print("\nAvailable animation paths:")
    for i, p in enumerate(all_paths, 1):
        print(f"{i}. {p}")

    # 3. Let user select a path
    try:
        choice = int(input("\nSelect a path by number: ").strip())
        selected_path = all_paths[choice - 1]
    except (ValueError, IndexError):
        fallback = 'general' if 'general' in all_paths else all_paths[0]
        print(f"❌ Invalid input. Using default path: '{fallback}'")
        selected_path = fallback

    # 4. Sample position over time (from 0 to stop_time, step = 0.002s)
    dt = 0.002
    max_t = player.stop_time
    times = np.arange(0, max_t + dt, dt)
    xs, ys = [], []

    print(f"\nComputing position data at {len(times)} time points...")
    for t in times:
        result, valid = player.play_frame(t, path=selected_path)
        if valid and 'position' in result:
            pos = result['position']
            # Safely convert to float (handles np.float64, array scalars, etc.)
            x_val = float(pos[0]) if hasattr(pos[0], '__float__') else 0.0
            y_val = float(pos[1]) if hasattr(pos[1], '__float__') else 0.0
            xs.append(x_val)
            ys.append(y_val)
        else:
            # If out of range, extend last known value (or zero)
            xs.append(xs[-1] if xs else 0.0)
            ys.append(ys[-1] if ys else 0.0)

    xs = np.array(xs)
    ys = np.array(ys)

    # 5. Plot setup
    fig, ax = plt.subplots(figsize=(10, 6))
    plt.subplots_adjust(left=0.25)  # Leave space for buttons on the left

    line_x, = ax.plot(times, xs, label='X', color='tab:blue', linewidth=1.8)
    line_y, = ax.plot(times, ys, label='Y', color='tab:orange', linewidth=1.8)

    ax.set_xlabel("Time (seconds)")
    ax.set_ylabel("Position Value")
    ax.set_title(f"Position Curve for Path '{selected_path}' (Duration: {max_t:.3f}s)")
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend()

    # Initial visibility state
    visible_x = True
    visible_y = True

    # 6. Toggle functions with dynamic button labels
    def toggle_x(event):
        nonlocal visible_x
        visible_x = not visible_x
        line_x.set_visible(visible_x)
        btn_x.label.set_text('Hide X' if visible_x else 'Show X')
        fig.canvas.draw_idle()

    def toggle_y(event):
        nonlocal visible_y
        visible_y = not visible_y
        line_y.set_visible(visible_y)
        btn_y.label.set_text('Hide Y' if visible_y else 'Show Y')
        fig.canvas.draw_idle()

    # Button positions: [left, bottom, width, height]
    ax_btn_x = plt.axes([0.02, 0.85, 0.08, 0.05])
    ax_btn_y = plt.axes([0.02, 0.78, 0.08, 0.05])

    btn_x = Button(ax_btn_x, 'Hide X', color='lightblue')
    btn_y = Button(ax_btn_y, 'Hide Y', color='lightsalmon')

    btn_x.on_clicked(toggle_x)
    btn_y.on_clicked(toggle_y)

    print("✅ Plot ready. Displaying window...")
    plt.show()


if __name__ == '__main__':
    main()