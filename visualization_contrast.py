import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from matplotlib.lines import Line2D
import time

# Import your original AnimationPlayer without modification
from animation_player import AnimationPlayer


def sample_animation_data(player, selected_path, dt, max_t):
    """Sample animation data at specified path with given time step"""
    times = np.arange(0, max_t + dt, dt)
    xs, ys = [], []
    
    print(f"  Sampling precision: {dt:.4f}s, Sample points: {len(times)}")
    start_time = time.time()
    
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
    
    computation_time = time.time() - start_time
    xs = np.array(xs)
    ys = np.array(ys)
    
    print(f"  Computation time: {computation_time:.3f}s")
    return times, xs, ys, computation_time


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

    # 4. Define different sampling precision levels (in seconds)
    sampling_precisions = [0.001, 0.002, 0.005, 0.01, 0.02, 0.05]
    precision_labels = [f'{dt*1000:.1f}ms' for dt in sampling_precisions]
    
    print(f"\n📊 Comparing the following sampling precisions: {', '.join(precision_labels)}")
    print("=" * 50)

    # 5. Sample data for each precision level
    all_data = []
    max_t = player.stop_time
    
    for i, dt in enumerate(sampling_precisions):
        print(f"\n[{i+1}/{len(sampling_precisions)}] Processing sampling precision {precision_labels[i]}:")
        times, xs, ys, comp_time = sample_animation_data(player, selected_path, dt, max_t)
        all_data.append({
            'times': times,
            'xs': xs,
            'ys': ys,
            'dt': dt,
            'label': precision_labels[i],
            'comp_time': comp_time
        })

    # 6. Plot setup
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    plt.subplots_adjust(left=0.1, right=0.85, top=0.92, bottom=0.1, hspace=0.3)
    
    # Color mapping - assign different colors for different precisions
    colors = plt.cm.viridis(np.linspace(0, 1, len(sampling_precisions)))
    
    # Store line objects for toggle display
    lines_x = []
    lines_y = []
    legend_elements = []
    
    # Plot X-axis position curves
    for i, data in enumerate(all_data):
        line_x, = ax1.plot(data['times'], data['xs'], 
                          label=f"X-{data['label']}", 
                          color=colors[i], 
                          linewidth=1.5,
                          alpha=0.8)
        lines_x.append(line_x)
        
        # Add legend elements
        legend_elements.append(Line2D([0], [0], color=colors[i], lw=2, 
                                    label=f"X-{data['label']} ({len(data['times'])} pts)"))
    
    ax1.set_xlabel("Time (seconds)")
    ax1.set_ylabel("X Position Value")
    ax1.set_title(f"X Position Curve Comparison - Path '{selected_path}' (Duration: {max_t:.3f}s)")
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.02, 1))

    # Clear legend elements for Y-axis
    legend_elements = []
    
    # Plot Y-axis position curves
    for i, data in enumerate(all_data):
        line_y, = ax2.plot(data['times'], data['ys'], 
                          label=f"Y-{data['label']}", 
                          color=colors[i], 
                          linewidth=1.5,
                          alpha=0.8)
        lines_y.append(line_y)
        
        # Add legend elements
        legend_elements.append(Line2D([0], [0], color=colors[i], lw=2, 
                                    label=f"Y-{data['label']} ({len(data['times'])} pts)"))

    ax2.set_xlabel("Time (seconds)")
    ax2.set_ylabel("Y Position Value")
    ax2.set_title(f"Y Position Curve Comparison - Path '{selected_path}' (Duration: {max_t:.3f}s)")
    ax2.grid(True, linestyle='--', alpha=0.6)
    ax2.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.02, 1))

    # 7. Create interactive buttons
    # Initial visibility states
    visibility_states = [True] * len(sampling_precisions)
    
    def create_toggle_function(index):
        """Create function to toggle display of specific precision"""
        def toggle(event):
            nonlocal visibility_states
            visibility_states[index] = not visibility_states[index]
            
            # Update visibility of corresponding lines
            lines_x[index].set_visible(visibility_states[index])
            lines_y[index].set_visible(visibility_states[index])
            
            # Update button label
            btn_label = f'Hide {precision_labels[index]}' if visibility_states[index] else f'Show {precision_labels[index]}'
            buttons[index].label.set_text(btn_label)
            
            fig.canvas.draw_idle()
        return toggle
    
    # Create buttons
    buttons = []
    button_height = 0.04
    button_spacing = 0.005
    start_y = 0.9 - (len(sampling_precisions) * (button_height + button_spacing))
    
    for i in range(len(sampling_precisions)):
        # Left button area
        ax_btn = plt.axes([0.02, start_y + i * (button_height + button_spacing), 0.12, button_height])
        btn_label = f'Hide {precision_labels[i]}'
        btn = Button(ax_btn, btn_label, color=colors[i])
        btn.on_clicked(create_toggle_function(i))
        buttons.append(btn)

    # 8. Display performance statistics
    stats_text = "Performance Statistics:\n"
    stats_text += "=" * 25 + "\n"
    for data in all_data:
        points = len(data['times'])
        comp_time = data['comp_time']
        rate = points / comp_time if comp_time > 0 else 0
        stats_text += f"{data['label']}: {points} pts, {comp_time:.3f}s, {rate:.0f} pts/s\n"
    
    # Add statistics text to bottom left of figure
    fig.text(0.02, 0.02, stats_text, fontsize=9, 
             verticalalignment='bottom', 
             bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.7))

    print("\n✅ Plot ready. Displaying window...")
    print("💡 Tip: Click left buttons to toggle visibility of different precision curves")
    plt.show()


if __name__ == '__main__':
    main()