from PyQt5.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from matplotlib import rcParams

# 指定中文字体
rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体
rcParams['axes.unicode_minus'] = False  # 解决保存图像时负号'-'显示为方块的问题

class ElongationPlotWindow(QWidget):
    '''
    绘制各光斑Elongation变化图表
    '''
    def __init__(self):
        super().__init__()
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvas(self.fig)

        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)

    def update_plot(self, elongation_data):
        self.ax.clear()
        data_length = len(elongation_data['bright_l'])
        start_index = max(0, data_length - 30)
        x = list(range(start_index, data_length))

        name_zh_dic = {'bright_l':"左亮斑",'bright_m':"中亮斑",'bright_r':"右亮斑"}
        
        for name, elongations in elongation_data.items():
            elongations_last_30 = elongations[-30:]
            self.ax.plot(x, [elong - elongations[0] for elong in elongations_last_30], label=name_zh_dic[name])

        self.ax.set_ylim([-0.15, 0.1])
        self.ax.axhline(y=0, color='r', linestyle='--', label="参照线")
        self.ax.grid(True)
        self.ax.legend()
        # self.ax.set_xlabel('Image Index')
        self.ax.set_ylabel('拉伸率')
        # self.canvas.draw()
        # 刷新图表
        self.canvas.draw_idle()


class AreaPlotWindow(QWidget):
    '''
    绘制各光斑Area变化图表
    '''
    def __init__(self):
        super().__init__()
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvas(self.fig)

        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)

    def update_plot(self, area_data):
        self.ax.clear()
        data_length = len(area_data['bright_l'])
        start_index = max(0, data_length - 30)
        x = list(range(start_index, data_length))

        name_zh_dic = {'bright_l':"左亮斑",'bright_m':"中亮斑",'bright_r':"右亮斑"}

        for name, areas in area_data.items():
            areas_last_30 = areas[-30:]
            self.ax.plot(x, [area - areas[0] for area in areas_last_30], label=name_zh_dic[name], marker='o')

        self.ax.set_ylim([-1000, 1000])
        self.ax.axhline(y=0, color='r', linestyle='--', label="参照线")
        self.ax.grid(True)
        self.ax.legend()
        # self.ax.set_xlabel('Image Index')
        self.ax.set_ylabel('面积')
        # self.canvas.draw()
        # 刷新图表
        self.canvas.draw_idle()
        # 实时更新图表
        # self.canvas.flush_events()

class Std2minPlotWindow(QWidget):
    '''
    绘制暗斑区域参数变化图表
    '''
    def __init__(self):
        super().__init__()
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvas(self.fig)

        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)

    def update_plot(self, std2min_data):
        self.ax.clear()
        data_length = len(std2min_data)
        start_index = max(0, data_length - 30)
        x = list(range(start_index, data_length))

        std2min_data_last_30 = std2min_data[-30:]
        self.ax.plot(x, [std2min - std2min_data[0] for std2min in std2min_data_last_30], label='暗斑', marker='o')
        self.ax.set_ylim([-1,3])
        self.ax.axhline(y=0, color='r', linestyle='--', label="参照线")
        self.ax.grid(True)
        self.ax.legend()
        # self.ax.set_xlabel('Image Index')
        self.ax.set_ylabel('标准差/最小值')
        # self.canvas.draw()
        # 刷新图表
        self.canvas.draw_idle()
        # 实时更新图表
        # self.canvas.flush_events()


class BrightnessPlotWindow(QWidget):
    '''
    绘制亮度参数变化图表
    '''
    def __init__(self):
        super().__init__()
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvas(self.fig)

        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)

    def update_plot(self, brightness_data):
        self.ax.clear()
        data_length = len(brightness_data)
        start_index = max(0, data_length - 30)
        x = list(range(start_index, data_length))

        brightness_last_30 = brightness_data[-30:]
        self.ax.plot(x, [bright - brightness_data[0] for bright in brightness_last_30], label='亮度', marker='o')
        self.ax.set_ylim([-20,20])
        self.ax.axhline(y=0, color='r', linestyle='--', label="参照线")
        self.ax.grid(True)
        self.ax.legend()
        # self.ax.set_xlabel('Image Index')
        self.ax.set_ylabel('亮度')
        # self.canvas.draw()
        # 刷新图表
        self.canvas.draw_idle()
        # 实时更新图表
        # self.canvas.flush_events()


class IntegratedPlotWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("综合图表分析")
        self.setGeometry(100, 100, 900, 600)
        self.setMinimumSize(640,480)

        # 创建标签页
        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)

        # 添加各个图表到标签页
        self.elongation_tab = ElongationPlotWindow()
        self.area_tab = AreaPlotWindow()
        self.std2min_tab = Std2minPlotWindow()
        self.brightness_tab = BrightnessPlotWindow()

        self.tabs.addTab(self.elongation_tab, "拉伸率")
        self.tabs.addTab(self.area_tab, "面积")
        self.tabs.addTab(self.std2min_tab, "标准差/最小值")
        self.tabs.addTab(self.brightness_tab, "亮度")

    def update_plots(self, elongation_data, area_data, std2min_data, brightness_data):
        self.elongation_tab.update_plot(elongation_data)
        self.area_tab.update_plot(area_data)
        self.std2min_tab.update_plot(std2min_data)
        self.brightness_tab.update_plot(brightness_data)

# class HistPlotWindow(QMainWindow):
#     '''
#     绘制暗斑区域参数变化图表
#     '''
#     def __init__(self):
#         super().__init__()

#         self.setWindowTitle("Hist of Params")
#         self.setGeometry(1300, 100, 600, 400)

#         self.fig, self.ax = plt.subplots(figsize=(6, 4))
#         self.canvas = FigureCanvas(self.fig)
#         self.setCentralWidget(self.canvas)

#     def update_plot(self, param_data):
#         self.ax.clear()

#         bin_width = 0.1
#         bins = np.arange(min(param_data), max(param_data) + bin_width, bin_width)

#         self.ax.hist(param_data, bins=bins, label='param')
#         self.ax.legend(labels = 'param')
#         self.ax.set_xlabel('Value Intervals')
#         self.ax.set_ylabel('Frequency')
#         self.canvas.draw()

