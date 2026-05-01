import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout

from typing import List, Tuple
class AnimGraphWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        self.layout = QVBoxLayout()
        self.plot_widget = pg.PlotWidget()
        self.layout.addWidget(self.plot_widget)
        self.setLayout(self.layout)

    def update_plot(self, points: List[Tuple[float, float]]):
        self.plot_widget.clear()
        x_vals = [point[0] for point in points]
        y_vals = [point[1] for point in points]
        curve = self.plot_widget.plot(x_vals, y_vals, pen=(255, 255, 255))