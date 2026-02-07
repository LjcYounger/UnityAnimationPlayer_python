import os
import sys
from typing import Dict, Any
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QSlider
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPixmap, QPainter, QTransform

from pyside_animation_player import PysideAnimationPlayer


class AnimationDisplayWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(400, 300)
        self.setStyleSheet("""
            QLabel {
                background-color: #1e1e1e;
                border: 1px solid #444;
            }
        """)
        
        self.original_pixmap = None
        self.position = (0, 0)
        self.scale = (1.0, 1.0)
        self.rotation = 0.0
        self.center_pos = (200, 150)
        
    def load_image(self, image_path: str):
        if os.path.exists(image_path):
            self.original_pixmap = QPixmap(image_path)
            self.update_display()
            return True
        else:
            print(f"Image not found: {image_path}")
            self.original_pixmap = QPixmap(400, 300)
            self.original_pixmap.fill(Qt.transparent)
            
            painter = QPainter(self.original_pixmap)
            painter.setPen(Qt.red)
            painter.drawEllipse(150, 100, 100, 100)
            painter.drawLine(200, 50, 200, 250)
            painter.drawLine(100, 150, 300, 150)
            painter.end()
            
            self.update_display()
            return False
    
    def apply_transform(self, frame_data: Dict[str, Any]):
        if not frame_data:
            return
        
        if 'position' in frame_data:
            pos_data = frame_data['position']
            if len(pos_data) >= 2:
                self.position = pos_data
        
        if 'scale' in frame_data:
            scale_data = frame_data['scale']
            if len(scale_data) >= 2:
                self.scale = scale_data
        
        if 'rotation' in frame_data:
            self.rotation = frame_data['rotation']
        elif 'euler' in frame_data:
            self.rotation = frame_data['euler']
        self.update_display()
    
    def update_display(self):
        if self.original_pixmap is None:
            return
        
        width = max(1, int(self.original_pixmap.width() * self.scale[0]))
        height = max(1, int(self.original_pixmap.height() * self.scale[1]))
        
        scaled_pixmap = self.original_pixmap.scaled(
            width, height,
            Qt.IgnoreAspectRatio, Qt.SmoothTransformation
        )
        
        transform = QTransform()
        transform.translate(width / 2, height / 2)
        transform.rotate(self.rotation, Qt.ZAxis)
        transform.translate(-width / 2, -height / 2)
        rotated_pixmap = scaled_pixmap.transformed(transform, Qt.SmoothTransformation)
        
        final_pixmap = QPixmap(400, 300)
        final_pixmap.fill(Qt.transparent)
        
        painter = QPainter(final_pixmap)
        
        final_x = self.center_pos[0] + self.position[0] - rotated_pixmap.width() / 2
        final_y = self.center_pos[1] - self.position[1] - rotated_pixmap.height() / 2
        
        painter.drawPixmap(int(final_x), int(final_y), rotated_pixmap)
        
        painter.setPen(Qt.green)
        painter.drawEllipse(self.center_pos[0] - 3, self.center_pos[1] - 3, 6, 6)
        
        painter.end()
        
        self.setPixmap(final_pixmap)
    
    def reset_transform(self):
        self.position = (0, 0)
        self.scale = (1.0, 1.0)
        self.rotation = 0.0
        self.update_display()


class AnimationTestWindow(QMainWindow):

    anim_signal = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("2D Animation Player")
        self.setGeometry(100, 100, 800, 600)
        
        self.anim_player = None
        self.anim_folder = "examples/AnimationClip"
        self.image_folder = "Images"
        self.animation_files = []
        self.current_anim = ""
        self.current_path = "general"
        self.current_time = 0.0
        self.animation_running = False
        
        self.anim_signal.connect(self.on_animation_frame)

        self.init_ui()
        self.load_animation_list()
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Top controls
        top_layout = QHBoxLayout()
        
        self.file_combo = QComboBox()
        self.file_combo.setMinimumWidth(150)
        self.file_combo.currentTextChanged.connect(self.on_file_changed)
        top_layout.addWidget(QLabel("Animation:"))
        top_layout.addWidget(self.file_combo)
        
        self.path_combo = QComboBox()
        self.path_combo.setMinimumWidth(120)
        self.path_combo.currentTextChanged.connect(self.on_path_changed)
        top_layout.addWidget(QLabel("Path:"))
        top_layout.addWidget(self.path_combo)
        
        top_layout.addStretch()
        
        layout.addLayout(top_layout)
        
        # Display area
        self.display_widget = AnimationDisplayWidget()
        layout.addWidget(self.display_widget, 1)
        
        # Bottom controls
        bottom_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("Play")
        self.play_btn.setMinimumWidth(80)
        self.play_btn.clicked.connect(self.toggle_play)
        bottom_layout.addWidget(self.play_btn)
        
        bottom_layout.addWidget(QLabel("Speed:"))
        
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(10, 200)  # 0.1x - 2.0x
        self.speed_slider.setValue(100)  # 1.0x
        self.speed_slider.setMaximumWidth(150)
        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        bottom_layout.addWidget(self.speed_slider)
        
        self.speed_label = QLabel("1.0x")
        self.speed_label.setMinimumWidth(40)
        bottom_layout.addWidget(self.speed_label)
        
        bottom_layout.addStretch()
        
        self.time_label = QLabel("0.00 / 0.00s")
        bottom_layout.addWidget(self.time_label)
        
        layout.addLayout(bottom_layout)
    
    def load_animation_list(self):
        if not os.path.exists(self.anim_folder):
            print(f"Error: Animation folder '{self.anim_folder}' not found")
            return
        
        self.animation_files = [f for f in os.listdir(self.anim_folder) if f.endswith('.anim')]
        self.file_combo.clear()
        
        if self.animation_files:
            self.file_combo.addItems([os.path.splitext(f)[0] for f in self.animation_files])
            print(f"Found {len(self.animation_files)} animation files")
        else:
            print("No animation files found")
            self.file_combo.addItem("No files")
    
    def on_file_changed(self, anim_name):
        if not anim_name or anim_name == "No files":
            return
        
        self.current_anim = anim_name
        anim_path = os.path.join(self.anim_folder, anim_name + '.anim')
        try:
            self.anim_player = PysideAnimationPlayer(
                signal=self.anim_signal,
                file_path=anim_path,
                stop_time=None, 
                path='general'
            )
            
            # Update path combo
            self.path_combo.clear()
            if self.anim_player.anim:
                paths = list(self.anim_player.anim.keys())
                self.path_combo.addItems(paths)
                if paths:
                    self.current_path = paths[0]
                    self.anim_player.parameters['path'] = self.current_path
                    print(f"Using path: {self.current_path}")
                else:
                    print("No paths found in animation")
            
            image_path = os.path.join(self.image_folder, f"{anim_name}.png")
            if not os.path.exists(image_path):
                image_path = self.image_folder
            
            self.display_widget.load_image(image_path)
            
            duration = self.anim_player.stop_time
            self.time_label.setText(f"0.00 / {duration:.2f}s")
            
            print(f"Loaded: {anim_name}.anim (Duration: {duration:.2f}s)")

            self.display_widget.reset_transform()
            
        except Exception as e:
            print(f"Failed to load animation: {str(e)}")
    
    def on_path_changed(self, path_name):
        if path_name and self.anim_player:
            self.current_path = path_name
            self.anim_player.parameters['path'] = path_name
            print(f"Switched to path: {path_name}")

            self.display_widget.reset_transform()
    
    def toggle_play(self):
        if not self.anim_player:
            return
        
        if self.animation_running:
            self.pause_animation()
        else:
            self.play_animation()
    
    def play_animation(self):
        if self.anim_player:
            self.animation_running = True
            self.play_btn.setText("Pause")
            self.anim_player.play()
    
    def pause_animation(self):
        if self.anim_player:
            self.animation_running = False
            self.play_btn.setText("Play")
            self.anim_player.mode = 0
            self.anim_player.timer.stop()
    
    def on_speed_changed(self, value):
        speed = value / 100.0
        self.speed_label.setText(f"{speed:.1f}x")
        if self.anim_player:
            self.anim_player.delta_t = 1/60 / speed
    
    def on_animation_frame(self, frame_data):
        self.display_widget.apply_transform(frame_data)
        
        if self.anim_player:
            self.current_time = self.anim_player.t
            duration = self.anim_player.stop_time
            self.time_label.setText(f"{self.current_time:.2f} / {duration:.2f}s")
            
            if self.current_time >= duration and not self.anim_player.playable:
                self.pause_animation()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = AnimationTestWindow()
    window.show()
    
    sys.exit(app.exec())


main()