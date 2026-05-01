from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt


class DarkScreenWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.ToolTip)
        self.setStyleSheet("background-color: black;")
        size=self.screen().availableGeometry()
        self.setGeometry(0,0,size.width(),size.height())
        self.setWindowOpacity(0.6)