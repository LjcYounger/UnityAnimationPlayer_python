# Base Class
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal
from pyside_animation_player import PysideAnimationPlayer

class PopupWindow(QWidget):
    anim_signal = Signal(dict)

    def __init__(self, anim='examples/AnimationClip/UIAni_Popup_System.anim', **kwargs):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

        if anim == 'examples/AnimationClip/UIAni_Popup_System.anim':
            kwargs.setdefault('path', 'Center/Popup')
            kwargs.setdefault('Pratio', (1, 0.5))
        self.anim_signal.connect(self.anim_signal_received)

        self.animation_player = PysideAnimationPlayer(self.anim_signal, anim, kwargs.get('stop_time', None), **kwargs)
    def play_anim(self, mode=1, initial_time=0):
        self.position0 = (self.pos().x(), self.pos().y())
        self.move(10000, 10000)
        self.show()
        self.animation_player.set_mode(mode)
        self.animation_player.set_time(initial_time)
        self.animation_player.play()

    def anim_signal_received(self, dic):
        position = dic.get('position', (0, 0))
        self.move(*[int(x - y) for x, y in zip(self.position0, position)])




# Example Class
from PySide6.QtWidgets import QLabel, QVBoxLayout, QPushButton

class ExamplePopupWindow(PopupWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("A Popup Window")
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)
        self.setFixedSize(400,210)
        center=self.screen().availableGeometry().center()
        self.move(center.x()-410/2, center.y()-210/2)

        self.label = QLabel("This is a popup window!")
        self.fast_button = QPushButton("Fast Replay")
        self.fast_button.clicked.connect(lambda: self.play_anim(1))
        self.slow_button = QPushButton("Slow Replay")
        self.slow_button.clicked.connect(lambda: self.play_anim(0.1))
        self.reverse_button = QPushButton("Reverse Replay")
        self.reverse_button.clicked.connect(lambda: self.play_anim(-1, self.animation_player.stop_time))

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.fast_button)
        self.layout.addWidget(self.slow_button)
        self.layout.addWidget(self.reverse_button)

        self.setLayout(self.layout)

        self.play_anim(1)

def main():
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = ExamplePopupWindow()
    window.show()
    sys.exit(app.exec_())

main()
