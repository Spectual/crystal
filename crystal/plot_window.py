from PyQt5.QtWidgets import QMainWindow
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import numpy as np

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
            self.ax.plot(x, [elong - elongations[0] for elong in elongations], label=name)

        self.ax.plot(x, [0 for i in x], label="ori", color='r')
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
        self.ax.plot(x, [0 for i in x], label="ori", color='r')
        self.ax.legend()
        self.ax.set_xlabel('Image Index')
        self.ax.set_ylabel('Area')
        self.canvas.draw()

class Std2minPlotWindow(QMainWindow):
    '''
    绘制暗斑区域参数变化图表
    '''
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Std2min Changes")
        self.setGeometry(1300, 100, 600, 400)

        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvas(self.fig)
        self.setCentralWidget(self.canvas)

    def update_plot(self, std2min_data):
        self.ax.clear()

        x = list(range(len(std2min_data)))
        self.ax.plot(x, [std2min - std2min_data[0] for std2min in std2min_data], label='dark spot', marker='o')
        self.ax.plot(x, [0 for i in x], label="ori", color='r')
        self.ax.legend()
        self.ax.set_xlabel('Image Index')
        self.ax.set_ylabel('Std2min')
        self.canvas.draw()

class BrightnessPlotWindow(QMainWindow):
    '''
    绘制亮度参数变化图表
    '''
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Brightness Changes")
        self.setGeometry(1300, 100, 600, 400)

        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvas(self.fig)
        self.setCentralWidget(self.canvas)

    def update_plot(self, brightness_data):
        self.ax.clear()

        x = list(range(len(brightness_data)))
        self.ax.plot(x, [bright - brightness_data[0] for bright in brightness_data], label='brightness', marker='o')
        self.ax.plot(x, [0 for i in x], label="ori", color='r')
        self.ax.legend()
        self.ax.set_xlabel('Image Index')
        self.ax.set_ylabel('Brightness')
        self.canvas.draw()

class HistPlotWindow(QMainWindow):
    '''
    绘制暗斑区域参数变化图表
    '''
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Hist of Params")
        self.setGeometry(1300, 100, 600, 400)

        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvas(self.fig)
        self.setCentralWidget(self.canvas)

    def update_plot(self, param_data):
        self.ax.clear()

        bin_width = 0.1
        bins = np.arange(min(param_data), max(param_data) + bin_width, bin_width)

        self.ax.hist(param_data, bins=bins, label='param')
        self.ax.legend(labels = 'param')
        self.ax.set_xlabel('Value Intervals')
        self.ax.set_ylabel('Frequency')
        self.canvas.draw()


