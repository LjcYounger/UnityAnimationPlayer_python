from functools import wraps
from pathlib import Path
from dataclasses import dataclass
import time
import platform
import os
import sys

# Ensure src/ is on the path for unity_animation_player imports
_src_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src')
if _src_path not in sys.path:
    sys.path.insert(0, os.path.abspath(_src_path))

from PySide6.QtWidgets import QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QWidget
from PySide6.QtCore import Qt, QUrl, Slot, Signal, QObject
from PySide6.QtQuickWidgets import QQuickWidget

# 导入消息处理相关模块
from PySide6.QtCore import qInstallMessageHandler, QtMsgType

from unity_animation_player import SignalAnimationPlayer
from .popup_window import PopupWindow
from .graph_window import AnimGraphWidget

DARK_SCREEN_WINDOW = platform.system() == "Windows"

def timer(func):
    @wraps(func)  # 保留原函数的元数据
    def wrapper(*args, **kwargs):
        start = time.perf_counter()  # 使用高精度计时器
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__} 耗时: {end - start:.8f} 秒")
        return result
    return wrapper


# 定义消息处理器
def qml_message_handler(mode, context, message):
    """
    捕获QML控制台输出信息
    Args:
        mode: 消息类型 (QtDebugMsg, QtWarningMsg, QtCriticalMsg等)
        context: 消息上下文 (包含文件、行号等信息)
        message: 实际的消息内容
    """
    message_types = {
        QtMsgType.QtDebugMsg: "DEBUG",
        QtMsgType.QtWarningMsg: "WARNING", 
        QtMsgType.QtCriticalMsg: "CRITICAL",
        QtMsgType.QtFatalMsg: "FATAL",
        QtMsgType.QtInfoMsg: "INFO"
    }
    
    msg_type_str = message_types.get(mode, "UNKNOWN")
    
    # 输出到Python控制台
    if context.file:
        print(f"[QML {msg_type_str}] {os.path.basename(context.file)}:{context.line}: {message}")
    else:
        print(f"[QML {msg_type_str}] {message}")


# 在导入模块后立即安装消息处理器
qInstallMessageHandler(qml_message_handler)


@dataclass
class ButtonAnimationData(QObject):
    """避免Signal只能作为类属性创建而无法动态创建的问题"""
    button_name: str
    player: SignalAnimationPlayer
    signal: Signal = Signal(dict)
    
    def __init__(self, button_name: str):
        super().__init__()
        self.button_name = button_name
        self.player = SignalAnimationPlayer(self.signal, f"examples/AnimationClip/UIAni_Button_Scale.anim")


class ExampleWindow(PopupWindow):
    button_data_dict = {}
    ball_animation_signal = Signal(dict)
    def __init__(self) -> None:
        super().__init__(dark_screen=DARK_SCREEN_WINDOW)
        self.setWindowTitle("Animation Window Demo")
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)
        init_size = (800, 400)
        self.resize(*init_size)
        center = self.screen().availableGeometry().center()
        self.move(center.x() - init_size[0] / 2, center.y() - init_size[1] / 2)

        main_layout = QVBoxLayout()
        
        #self.graph_widget = AnimGraphWidget()
        #self.graph_widget.setFixedSize(800, 200)
        #main_layout.addWidget(self.graph_widget)

        self.quick_widget = QQuickWidget()
        self.quick_widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
        self.quick_widget.setSource(QUrl.fromLocalFile(Path(__file__).parent / "example.qml"))
        
        self.quick_widget.rootContext().setContextProperty("exampleWindow", self)
        self.root_obj = self.quick_widget.rootObject()

        main_layout.addWidget(self.quick_widget)
        self.setLayout(main_layout)

        self.animated_buttons = self.root_obj.property("animatedButtons").toVariant().keys()
        print(self.animated_buttons)

        self.setup_multiple_animations(self.animated_buttons)

        self.ball_animation_signal.connect(self.on_ball_signal_received)
        #self.ball_animation_player = SignalAnimationPlayer(self.ball_animation_signal, "examples/AnimationClip/Hihumi_Original_TSS_Interaction01.anim", stop_time=None, position_ratio=(-24000, -6000), path="bone_root/Bip001")
        self.ball_animation_player = SignalAnimationPlayer(self.ball_animation_signal, "examples/AnimationClip/T.anim", stop_time=None, position_ratio=(9, 4))
        #self.ball_animation_player = SignalAnimationPlayer(self.ball_animation_signal, "examples/AnimationClip/circle.anim", stop_time=None, position_ratio=(100, 100))

        self.ball_animation_player.register_event('eventTriggered', self.event_triggered, ('data',))

        self.play_anim()
    
    def setup_multiple_animations(self, button_names):
        """为每个按钮设置动画播放器"""
        for button_name in button_names:
            # 创建按钮数据对象
            button_data = ButtonAnimationData(button_name)
            self.button_data_dict[button_name] = button_data

            # 连接信号到处理函数
            button_data.signal.connect(lambda data, btn=button_name: self.on_button_signal_received(btn, data))

    @Slot(float)
    def on_slider_value_changed(self, value):
        self.animation_player.set_mode(value)
        self.ball_animation_player.set_mode(value)
    @Slot()
    def replay_window_animation(self):
        if self.animation_player:
            self.animation_player.play()
    @Slot(str)
    def on_button_pressed(self, button_name):
        if button_name in self.button_data_dict:
            self.button_data_dict[button_name].player.play(0, mode=1)
    
    @Slot(str)
    def on_button_released(self, button_name):
        if button_name in self.button_data_dict:
            button_data = self.button_data_dict[button_name]
            button_data.player.play(button_data.player.stop_time, mode=-1)

    def on_button_signal_received(self, button_name, data):
        if data['playable']:
            scaleX, scaleY = data.get('scale', (None, None))
            scaleX = float(scaleX) if scaleX else None
            scaleY = float(scaleY) if scaleY else None

            self.root_obj.updateButtonTransform(button_name, None, scaleX, scaleY)

    @Slot()
    def on_ball_animation_button_pressed(self):
        self.ball_animation_player.play()


    def on_ball_signal_received(self, data):
        """处理小球动画"""
        if data['playable']:
            centerX, centerY = data.get('position', (None, None))
            centerX = float(centerX) if centerX else None
            centerY = float(centerY) if centerY else None

            scaleX, scaleY = data.get('scale', (None, None))
            scaleX = float(scaleX) if scaleX else None
            scaleY = float(scaleY) if scaleY else None

            rotationAngle = data.get('euler', None)
            rotationAngle = float(rotationAngle) if rotationAngle else None
            self.root_obj.enableBallTrail()
            self.root_obj.updateBallTransform(centerX, centerY, scaleX, scaleY, rotationAngle)
        else:
            self.root_obj.disableBallTrail()
            self.root_obj.resetBallTransform()

    def event_triggered(self, data):
        print(data)
    @Slot()
    def show_child_window(self):
        child_window = ChildWindow()


class ChildWindow(PopupWindow):
    def __init__(self):
        super().__init__(dark_screen=DARK_SCREEN_WINDOW)
        self.setWindowTitle("Notice")
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)
        self.setWindowModality(Qt.ApplicationModal)
        self.setFixedSize(250,120)
        center=self.screen().availableGeometry().center()
        self.move(center.x()-250/2, center.y()-120/2)

        layout=QVBoxLayout()
        #layout.addStretch()

        h_layout1 = QHBoxLayout()
        h_layout1.addStretch()
        self.textbox=QLabel()
        self.textbox.setText("This is a piece of information.")
        self.textbox.setStyleSheet("color: #456397;")
        self.textbox.setAlignment(Qt.AlignmentFlag.AlignCenter)  # 文本居中          # 固定宽度200px
        h_layout1.addWidget(self.textbox)
        h_layout1.addStretch()


        h_layout2 = QHBoxLayout()
        h_layout2.addStretch()
        self.button = QPushButton()
        self.button.setText("OK")
        self.button.setStyleSheet("color: #456397;")
        self.button.setFixedSize(120,40)
        self.button.clicked.connect(lambda: self.close())
        h_layout2.addWidget(self.button)
        h_layout2.addStretch()

        layout.addLayout(h_layout1)
        layout.addLayout(h_layout2)
        self.setLayout(layout)

        self.play_anim()