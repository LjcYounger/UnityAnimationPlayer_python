import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtGui import QPalette

from typing import List, Tuple
class AnimGraphWidget(QWidget):
    def __init__(self, left_title=False, title_width=100):
        super().__init__()
        
        self.layout = QHBoxLayout()

        self.title = None
        if left_title:
            self.title = QLabel()
            self.title.setFixedWidth(title_width)
            self.layout.addWidget(self.title)

        self.plot_widget = pg.PlotWidget()

        bg_color = self.palette().color(QPalette.Window)
        self.plot_widget.setBackground(bg_color)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.2)
        self.plot_widget.setStyleSheet("border: 1px solid rgb(0, 0, 0);")
        self.plot_widget.setAntialiasing(True)

        self.plot_item = self.plot_widget.getPlotItem()

        for axis in ['left', 'bottom', 'right', 'top']:
            ax = self.plot_item.getAxis(axis)
            ax.setPen((0, 0, 0))
            ax.setTextPen((0, 0, 0))

        self.layout.addWidget(self.plot_widget)
        self.setLayout(self.layout)

    def update_plot(self, points: List[Tuple[float, float]]):
        self.plot_widget.clear()
        x_vals = [point[0] for point in points]
        y_vals = [point[1] for point in points]
        curve = self.plot_widget.plot(x_vals, y_vals, pen=pg.mkPen('r', width=1))
        self.plot_widget.enableAutoRange()