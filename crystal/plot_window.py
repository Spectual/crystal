from PyQt5.QtWidgets import QMainWindow
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

class ElongationPlotWindow(QMainWindow):
    '''
    绘制各光斑Elongation变化图表
    '''
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Elongation Changes")
        self.setGeometry(1300, 100, 600, 400)

        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvas(self.fig)
        self.setCentralWidget(self.canvas)

    def update_plot(self, elongation_data):
        self.ax.clear()

        x = list(range(len(elongation_data['bright_l'])))
        for name, elongations in elongation_data.items():
            self.ax.plot(x, elongations, label=name)

        self.ax.legend()
        self.ax.set_xlabel('Image Index')
        self.ax.set_ylabel('Elongation')
        self.canvas.draw()


class AreaPlotWindow(QMainWindow):
    '''
    绘制各光斑Area变化图表
    '''
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Area Changes")
        self.setGeometry(700, 100, 600, 400)

        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvas(self.fig)
        self.setCentralWidget(self.canvas)

    def update_plot(self, area_data):
        self.ax.clear()

        x = list(range(len(area_data['bright_l'])))
        for name, areas in area_data.items():
            self.ax.plot(x, [area - areas[0] for area in areas], label=name, marker='o')

        self.ax.legend()
        self.ax.set_xlabel('Image Index')
        self.ax.set_ylabel('Area')
        self.canvas.draw()