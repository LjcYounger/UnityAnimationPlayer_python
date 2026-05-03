import os
import sys
from pathlib import Path
from dataclasses import asdict
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QFrame, QCheckBox, QDoubleSpinBox
)

from unity_animation_player import AnimationPlayer, PlayKwargs
from .qml_window_example_windows.graph_window import AnimGraphWidget

class InteractivePanel(QWidget):

    def __init__(self, animation_folder="examples/AnimationClip"):
        super().__init__()
        self.animation_folder = Path(animation_folder)
        self.animations = os.listdir(self.animation_folder)
        print(f"Found {len(self.animations)} animations in {self.animation_folder}: {', '.join(self.animations)}")

        self.play_kwargs = PlayKwargs()
        self.play_kwargs.path = 'general'
        self.play_kwargs.timeReverse = False
        self.play_kwargs.Eunit = ('z',)
        self.play_kwargs.Runit = ('w',)
        self.play_kwargs.Punit = ('x', 'y')
        self.play_kwargs.Preverse = False
        self.play_kwargs.Pratio = 1.0

        self.setup_ui()
        self.connect_signals()

        self.animation_name_combo.addItems(self.animations)
        self.update_animation(self.animations[0] if self.animations else '')
        
        # 新增：初始化时同步UI状态
        self.sync_ui_from_kwargs()

    def sync_ui_from_kwargs(self):
        """根据 self.play_kwargs 初始化 UI 控件的状态"""
        # 1. Time Reverse
        self.time_reverse_check.setChecked(self.play_kwargs.timeReverse)

        # 2. Euler Unit
        e_units = self.play_kwargs.Eunit if isinstance(self.play_kwargs.Eunit, tuple) else (self.play_kwargs.Eunit,)
        self.e_u_x_check.setChecked('x' in e_units)
        self.e_u_y_check.setChecked('y' in e_units)
        self.e_u_z_check.setChecked('z' in e_units)

        # 3. Rotation Unit
        r_units = self.play_kwargs.Runit if isinstance(self.play_kwargs.Runit, tuple) else (self.play_kwargs.Runit,)
        self.r_u_x_check.setChecked('x' in r_units)
        self.r_u_y_check.setChecked('y' in r_units)
        self.r_u_z_check.setChecked('z' in r_units)
        self.r_u_w_check.setChecked('w' in r_units)

        # 4. Position Unit
        p_units = self.play_kwargs.Punit if isinstance(self.play_kwargs.Punit, tuple) else (self.play_kwargs.Punit,)
        self.p_u_x_check.setChecked('x' in p_units)
        self.p_u_y_check.setChecked('y' in p_units)
        self.p_u_z_check.setChecked('z' in p_units)

        # 5. Position Reverse
        # 判断是否是 All 模式 (True/False) 还是 Tuple 模式
        if isinstance(self.play_kwargs.Preverse, bool):
            self.p_re_all_check.setChecked(self.play_kwargs.Preverse)
            # 如果 All 被勾选，下面的 xyz 应该不可用且未勾选
            self.p_re_x_check.setChecked(False)
            self.p_re_y_check.setChecked(False)
            self.p_re_z_check.setChecked(False)
        else:
            # Tuple 模式
            self.p_re_all_check.setChecked(False)
            reverses = self.play_kwargs.Preverse
            # 确保 reverses 是列表或元组以便索引检查
            if not isinstance(reverses, (list, tuple)):
                reverses = (reverses,)
            
            # 映射顺序: x, y, z
            checks = [self.p_re_x_check, self.p_re_y_check, self.p_re_z_check]
            for i, check in enumerate(checks):
                if i < len(reverses):
                    check.setChecked(bool(reverses[i]))
                else:
                    check.setChecked(False)

        # 6. Position Ratio
        if isinstance(self.play_kwargs.Pratio, (int, float)):
            # All 模式
            self.p_ra_all_check.setChecked(True)
            self.p_ra_all_spin.setValue(float(self.play_kwargs.Pratio))
            # 禁用单独的设置框
            self.p_ra_x_spin.setEnabled(False)
            self.p_ra_y_spin.setEnabled(False)
            self.p_ra_z_spin.setEnabled(False)
        else:
            # Tuple 模式
            self.p_ra_all_check.setChecked(False)
            ratios = self.play_kwargs.Pratio
            if not isinstance(ratios, (list, tuple)):
                ratios = (ratios,)
            
            spins = [self.p_ra_x_spin, self.p_ra_y_spin, self.p_ra_z_spin]
            for i, spin in enumerate(spins):
                if i < len(ratios):
                    spin.setValue(float(ratios[i]))
                else:
                    spin.setValue(1.0)
                
                # 启用单独的设置框
                spin.setEnabled(True)
            # 禁用 All 输入框
            self.p_ra_all_spin.setEnabled(False)

    def setup_ui(self):
        self.overall_layout = QVBoxLayout()

        self.head_layout = QHBoxLayout()
        self.kwargs_label = QLabel()
        self.head_layout.addWidget(self.kwargs_label)

        self.overall_layout.addLayout(self.head_layout)

        self.main_layout = QHBoxLayout()

        self.control_widget = QWidget()
        self.control_widget.setFixedWidth(400)
        self.control_layout = QVBoxLayout(self.control_widget)

        self.animation_name_layout = QHBoxLayout()
        self.label = QLabel('Animation Name')
        self.animation_name_layout.addWidget(self.label)
        self.animation_name_combo = QComboBox()
        self.animation_name_layout.addWidget(self.animation_name_combo)
        self.control_layout.addLayout(self.animation_name_layout)

        self.path_layout = QHBoxLayout()
        self.label_2 = QLabel('Path')
        self.path_layout.addWidget(self.label_2)
        self.path_combo = QComboBox()
        self.path_layout.addWidget(self.path_combo)
        self.control_layout.addLayout(self.path_layout)

        self.transform_layout = QHBoxLayout()
        self.label_14 = QLabel('Transform')
        self.transform_layout.addWidget(self.label_14)
        self.transform_combo = QComboBox()
        self.transform_layout.addWidget(self.transform_combo)
        self.control_layout.addLayout(self.transform_layout)

        self.time_reverse_check = QCheckBox()
        self.time_reverse_check.setText("Time Reverse")
        self.control_layout.addWidget(self.time_reverse_check)

        self.e_u_layout = QHBoxLayout()
        self.label_3 = QLabel('Euler Unit')
        self.e_u_layout.addWidget(self.label_3)
        self.e_u_x_check = QCheckBox('x')
        self.e_u_layout.addWidget(self.e_u_x_check)
        self.e_u_y_check = QCheckBox('y')
        self.e_u_layout.addWidget(self.e_u_y_check)
        self.e_u_z_check = QCheckBox('z')
        self.e_u_layout.addWidget(self.e_u_z_check)
        self.control_layout.addLayout(self.e_u_layout)

        self.r_u_layout = QHBoxLayout()
        self.label_4 = QLabel('Rotation Unit')
        self.r_u_layout.addWidget(self.label_4)
        self.r_u_x_check = QCheckBox('x')
        self.r_u_layout.addWidget(self.r_u_x_check)
        self.r_u_y_check = QCheckBox('y')
        self.r_u_layout.addWidget(self.r_u_y_check)
        self.r_u_z_check = QCheckBox('z')
        self.r_u_layout.addWidget(self.r_u_z_check)
        self.r_u_w_check = QCheckBox('w')
        self.r_u_layout.addWidget(self.r_u_w_check)
        self.control_layout.addLayout(self.r_u_layout)

        self.p_u_layout = QHBoxLayout()
        self.label_5 = QLabel('Position Unit')
        self.p_u_layout.addWidget(self.label_5)
        self.p_u_x_check = QCheckBox('x')
        self.p_u_layout.addWidget(self.p_u_x_check)
        self.p_u_y_check = QCheckBox('y')
        self.p_u_layout.addWidget(self.p_u_y_check)
        self.p_u_z_check = QCheckBox('z')
        self.p_u_layout.addWidget(self.p_u_z_check)
        self.control_layout.addLayout(self.p_u_layout)

        self.p_re_all_layout = QHBoxLayout()
        self.label_6 = QLabel('Position Reverse')
        self.p_re_all_layout.addWidget(self.label_6)
        self.p_re_all_check = QCheckBox('All')
        self.p_re_all_layout.addWidget(self.p_re_all_check)
        self.control_layout.addLayout(self.p_re_all_layout)

        self.p_re_xyz_layout = QHBoxLayout()
        self.label_7 = QLabel('OR')
        self.p_re_xyz_layout.addWidget(self.label_7)
        self.p_re_x_check = QCheckBox('x')
        self.p_re_xyz_layout.addWidget(self.p_re_x_check)
        self.p_re_y_check = QCheckBox('y')
        self.p_re_xyz_layout.addWidget(self.p_re_y_check)
        self.p_re_z_check = QCheckBox('z')
        self.p_re_xyz_layout.addWidget(self.p_re_z_check)
        self.control_layout.addLayout(self.p_re_xyz_layout)

        self.p_ra_all_layout = QHBoxLayout()
        self.label_9 = QLabel('Position Ratio')
        self.p_ra_all_layout.addWidget(self.label_9)
        self.p_ra_all_spin = QDoubleSpinBox()
        self.p_ra_all_spin.setObjectName(u"p_ra_all_spin")
        self.p_ra_all_spin.setMaximum(100)
        self.p_ra_all_spin.setSingleStep(0.01)
        self.p_ra_all_spin.setValue(1)
        self.p_ra_all_layout.addWidget(self.p_ra_all_spin)
        self.p_ra_all_check = QCheckBox('All')
        self.p_ra_all_layout.addWidget(self.p_ra_all_check)
        self.control_layout.addLayout(self.p_ra_all_layout)

        self.p_ra_xyz_layout = QHBoxLayout()
        self.label_8 = QLabel('OR')
        self.p_ra_xyz_layout.addWidget(self.label_8)
        self.p_ra_x_spin = QDoubleSpinBox()
        self.p_ra_x_spin.setMaximum(100)
        self.p_ra_x_spin.setSingleStep(0.01)
        self.p_ra_x_spin.setValue(1)
        self.p_ra_xyz_layout.addWidget(self.p_ra_x_spin)
        self.label_13 = QLabel('x')
        self.p_ra_xyz_layout.addWidget(self.label_13)
        self.p_ra_y_spin = QDoubleSpinBox()
        self.p_ra_y_spin.setMaximum(100)
        self.p_ra_y_spin.setSingleStep(0.01)
        self.p_ra_y_spin.setValue(1)
        self.p_ra_xyz_layout.addWidget(self.p_ra_y_spin)
        self.label_12 = QLabel('y')
        self.p_ra_xyz_layout.addWidget(self.label_12)
        self.p_ra_z_spin = QDoubleSpinBox()
        self.p_ra_z_spin.setMaximum(100)
        self.p_ra_z_spin.setSingleStep(0.01)
        self.p_ra_z_spin.setValue(1)
        self.p_ra_xyz_layout.addWidget(self.p_ra_z_spin)
        self.label_11 = QLabel('z')
        self.p_ra_xyz_layout.addWidget(self.label_11)
        self.control_layout.addLayout(self.p_ra_xyz_layout)

        self.control_layout.addStretch()
        
        self.main_layout.addWidget(self.control_widget)

        self.line = QFrame()
        self.line.setFrameShape(QFrame.VLine)
        self.main_layout.addWidget(self.line)

        self.graph_layout = QVBoxLayout()
        self.graph_widgets = [AnimGraphWidget(left_title=True) for _ in range(4)]
        for graph_widget in self.graph_widgets:
            self.graph_layout.addWidget(graph_widget)
        self.main_layout.addLayout(self.graph_layout)
        self.overall_layout.addLayout(self.main_layout)
        self.setLayout(self.overall_layout)

    def connect_signals(self):
        self.animation_name_combo.currentTextChanged.connect(self.update_animation)
        self.path_combo.currentTextChanged.connect(self.update_path)
        self.transform_combo.currentTextChanged.connect(self.update_transform)
        self.time_reverse_check.stateChanged.connect(self.on_time_reverse_changed)
        
        self.e_u_x_check.stateChanged.connect(self.on_euler_unit_changed)
        self.e_u_y_check.stateChanged.connect(self.on_euler_unit_changed)
        self.e_u_z_check.stateChanged.connect(self.on_euler_unit_changed)
        
        self.r_u_x_check.stateChanged.connect(self.on_rotation_unit_changed)
        self.r_u_y_check.stateChanged.connect(self.on_rotation_unit_changed)
        self.r_u_z_check.stateChanged.connect(self.on_rotation_unit_changed)
        self.r_u_w_check.stateChanged.connect(self.on_rotation_unit_changed)
        
        self.p_u_x_check.stateChanged.connect(self.on_position_unit_changed)
        self.p_u_y_check.stateChanged.connect(self.on_position_unit_changed)
        self.p_u_z_check.stateChanged.connect(self.on_position_unit_changed)
        
        self.p_re_all_check.stateChanged.connect(self.on_position_reverse_all_changed)
        self.p_re_x_check.stateChanged.connect(self.on_position_reverse_xyz_changed)
        self.p_re_y_check.stateChanged.connect(self.on_position_reverse_xyz_changed)
        self.p_re_z_check.stateChanged.connect(self.on_position_reverse_xyz_changed)
        
        self.p_ra_all_check.stateChanged.connect(self.on_position_ratio_all_changed)
        self.p_ra_all_spin.valueChanged.connect(self.on_position_ratio_all_value_changed)
        self.p_ra_x_spin.valueChanged.connect(self.on_position_ratio_xyz_changed)
        self.p_ra_y_spin.valueChanged.connect(self.on_position_ratio_xyz_changed)
        self.p_ra_z_spin.valueChanged.connect(self.on_position_ratio_xyz_changed)

    def update_animation(self, animation_name='T.anim'):
        if not animation_name or animation_name not in self.animations:
            return
        
        self.currect_animation = animation_name
        self.animation_player = AnimationPlayer(str(self.animation_folder / self.currect_animation))

        self.pathes = list(self.animation_player.anim.keys())
        self.path_combo.clear()
        self.path_combo.addItems(self.pathes)
        
        if self.pathes:
            self.update_path(self.pathes[0])

    def update_path(self, path_name='general'):
        self.play_kwargs.path = path_name
        if not hasattr(self, 'animation_player'):
            return
            
        self.current_path = path_name if path_name in self.pathes else self.pathes[0]
        
        if self.current_path in self.animation_player.anim:
            transforms = list(self.animation_player.anim[self.current_path].keys())
            current_transform = self.transform_combo.currentText()
            self.transform_combo.clear()
            self.transform_combo.addItems(transforms)
            self.transform_combo.setCurrentText(current_transform) if current_transform in transforms else None
        self.update_graph()
    def update_transform(self, transform_name='Position'):
        self.update_graph()
    def on_time_reverse_changed(self, state):
        self.play_kwargs.timeReverse = (state == 2)
        print(f"Time Reverse: {self.play_kwargs.timeReverse}")
        self.update_graph()

    def on_euler_unit_changed(self, state):
        units = []
        if self.e_u_x_check.isChecked():
            units.append('x')
        if self.e_u_y_check.isChecked():
            units.append('y')
        if self.e_u_z_check.isChecked():
            units.append('z')
        
        self.play_kwargs.Eunit = tuple(units) if units else 'z'
        print(f"Euler Unit: {self.play_kwargs.Eunit}")
        self.update_graph()

    def on_rotation_unit_changed(self, state):
        units = []
        if self.r_u_x_check.isChecked():
            units.append('x')
        if self.r_u_y_check.isChecked():
            units.append('y')
        if self.r_u_z_check.isChecked():
            units.append('z')
        if self.r_u_w_check.isChecked():
            units.append('w')
        
        self.play_kwargs.Runit = tuple(units) if units else 'w'
        print(f"Rotation Unit: {self.play_kwargs.Runit}")
        self.update_graph()

    def on_position_unit_changed(self, state):
        units = []
        reverses = []
        if self.p_u_x_check.isChecked():
            reverses.append(self.p_re_x_check.isChecked())
            units.append('x')
        if self.p_u_y_check.isChecked():
            reverses.append(self.p_re_y_check.isChecked())
            units.append('y')
        if self.p_u_z_check.isChecked():
            reverses.append(self.p_re_z_check.isChecked())
            units.append('z')
        
        if not reverses:
            self.play_kwargs.Preverse = False
        else:
            self.play_kwargs.Preverse = tuple(reverses)

        self.play_kwargs.Punit = tuple(units) if units else ('x', 'y')
        print(f"Position Unit: {self.play_kwargs.Punit}")
        self.update_graph()

    def on_position_reverse_all_changed(self, state):
        is_all_checked = (state == 2)
        
        self.p_re_x_check.setEnabled(not is_all_checked)
        self.p_re_y_check.setEnabled(not is_all_checked)
        self.p_re_z_check.setEnabled(not is_all_checked)
        
        if is_all_checked:
            self.play_kwargs.Preverse = True
            self.p_re_x_check.setChecked(False)
            self.p_re_y_check.setChecked(False)
            self.p_re_z_check.setChecked(False)
        else:
            self.on_position_reverse_xyz_changed()
        
        print(f"Position Reverse: {self.play_kwargs.Preverse}")
        self.update_graph()

    def on_position_reverse_xyz_changed(self, state=None):
        if self.p_re_all_check.isChecked():
            return
        
        reverses = []
        if self.p_u_x_check.isChecked():
            reverses.append(self.p_re_x_check.isChecked())
        if self.p_u_y_check.isChecked():
            reverses.append(self.p_re_y_check.isChecked())
        if self.p_u_z_check.isChecked():
            reverses.append(self.p_re_z_check.isChecked())
        
        if not reverses:
            self.play_kwargs.Preverse = False
        else:
            self.play_kwargs.Preverse = tuple(reverses)
        
        print(f"Position Reverse: {self.play_kwargs.Preverse}")
        self.update_graph()

    def on_position_ratio_all_changed(self, state):
        is_all_checked = (state == 2)
        
        self.p_ra_all_spin.setEnabled(is_all_checked)
        self.p_ra_x_spin.setEnabled(not is_all_checked)
        self.p_ra_y_spin.setEnabled(not is_all_checked)
        self.p_ra_z_spin.setEnabled(not is_all_checked)
        
        if is_all_checked:
            self.play_kwargs.Pratio = self.p_ra_all_spin.value()
            print(f"Position Ratio: {self.play_kwargs.Pratio}")
        else:
            self.on_position_ratio_xyz_changed()
        self.update_graph()

    def on_position_ratio_all_value_changed(self, value):
        if self.p_ra_all_check.isChecked():
            self.play_kwargs.Pratio = value
            print(f"Position Ratio: {self.play_kwargs.Pratio}")
        self.update_graph()

    def on_position_ratio_xyz_changed(self, value=None):
        if self.p_ra_all_check.isChecked():
            return
        
        ratios = [
            self.p_ra_x_spin.value(),
            self.p_ra_y_spin.value(),
            self.p_ra_z_spin.value()
        ]
        
        unique_ratios = set(ratios)
        if len(unique_ratios) == 1:
            self.play_kwargs.Pratio = ratios[0]
        else:
            self.play_kwargs.Pratio = tuple(ratios)
        
        print(f"Position Ratio: {self.play_kwargs.Pratio}")
        self.update_graph()

    def update_graph(self):
        if not self.play_kwargs.path: return

        self.kwargs_label.setText(', '.join((f'{key}={value}' for key, value in asdict(self.play_kwargs).items() if value is not None)))
        #print(asdict(self.play_kwargs))
        sample_data = self.animation_player.sample_range(sample_rate=0.002, t_start=None, t_end=None, **asdict(self.play_kwargs))
        sample_transform = self.transform_combo.currentText()
        if not sample_transform: return
        sample_units = self.play_kwargs.Punit if sample_transform == 'Position' \
                        else self.play_kwargs.Runit if sample_transform == 'Rotation' \
                        else self.play_kwargs.Eunit
        for graph_widget in self.graph_widgets:
            graph_widget.plot_widget.clear()
        for i, unit in enumerate(sample_units):
            sample_points = [(t, sample_data[t][sample_transform.lower()][i]) for t in sample_data.keys()]
            self.graph_widgets[i].update_plot(sample_points)
            self.graph_widgets[i].title.setText(f"{sample_transform} ({unit})")


def main():
    app = QApplication(sys.argv)
    
    interactive_panel = InteractivePanel()
    interactive_panel.show()
    
    sys.exit(app.exec())


main()