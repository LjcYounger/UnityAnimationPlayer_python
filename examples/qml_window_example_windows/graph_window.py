import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel

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

        self.plot_widget.showGrid(x=True, y=True, alpha=0.2)
        self.plot_widget.setStyleSheet("border-radius: 4px;border: 2px solid #455364")
        self.plot_widget.setAntialiasing(True)

        self.plot_item = self.plot_widget.getPlotItem()

        for axis in ['left', 'bottom', 'right', 'top']:
            ax = self.plot_item.getAxis(axis)
            ax.setPen('#DFE1E2')
            ax.setTextPen('#DFE1E2')

        self.layout.addWidget(self.plot_widget)
        self.setLayout(self.layout)

    def update_plot(self, points: List[Tuple[float, float]]):
        self.plot_widget.clear()
        x_vals = [point[0] for point in points]
        y_vals = [point[1] for point in points]
        curve = self.plot_widget.plot(x_vals, y_vals, pen=pg.mkPen('#DFE1E2', width=1))
        self.plot_widget.enableAutoRange()