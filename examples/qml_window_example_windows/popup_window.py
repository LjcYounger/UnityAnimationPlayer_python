import os
import sys

# Ensure src/ is on the path for unity_animation_player imports
_src_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src')
if _src_path not in sys.path:
    sys.path.insert(0, os.path.abspath(_src_path))

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal
from unity_animation_player import SignalAnimationPlayer

import time

from .dark_screen_window import DarkScreenWindow


class PopupWindow(QWidget):
    anim_signal = Signal(dict)

    def __init__(self, dark_screen=True, parent=None):
        super().__init__(parent=parent)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.animation_player = None
        self.dark_screen_window = None
        if dark_screen:
            self.dark_screen_window = DarkScreenWindow()
            self.dark_screen_window.show()

    def play_anim(self, **kwargs):
        """一键播放动画的高级封装"""
        anim = kwargs.get('anim', 'examples/AnimationClip/UIAni_Popup_System.anim')
        if anim == 'examples/AnimationClip/UIAni_Popup_System.anim' and not kwargs:
            kwargs.setdefault('path', 'Center/Popup')
            kwargs.setdefault('position_ratio', (1, 0.5))

        self.position0 = (self.pos().x(), self.pos().y())
        self.move(10000, 10000)
        self.show()

        self.anim_signal.connect(self.anim_signal_received)
        self.animation_player = SignalAnimationPlayer(self.anim_signal, anim, kwargs.get('stop_time', None), **kwargs)
        self.animation_player.play()

    def anim_signal_received(self, dic):
        position = dic.get('position', (0, 0))
        self.move(*[int(x - y) for x, y in zip(self.position0, position)])

    def closeEvent(self, event):
        if self.dark_screen_window:
            self.dark_screen_window.close()
