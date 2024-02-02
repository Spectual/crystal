from PyQt5.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout
from pyqtgraph import PlotWidget, mkPen, InfiniteLine
import pyqtgraph as pg
from PyQt5.QtGui import QColor, QFont


class PlotWindowBase(QWidget):
    def __init__(self, title, y_axis_label):
        super().__init__()
        self.plot_widget = PlotWidget()
        self.plot_widget.setTitle(title, size='10pt')
        # self.plot_widget.setLabel('left', y_axis_label, size='5pt')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setBackground('#EBECEE')  # 设置背景颜色为白色
        self.plot_widget.getAxis('left').setLabel(y_axis_label, color='r', size='10pt')
        self.plot_widget.getAxis('bottom').setStyle(tickFont=QFont("Arial", 10))
        self.plot_widget.getAxis('left').setStyle(tickFont=QFont("Arial", 10))

        layout = QVBoxLayout(self)
        layout.addWidget(self.plot_widget)

        # 用于存储数据的字典
        self.data_dict = {}

        # 预定义一些颜色
        self.colors = ['#4B89C1', '#DD4444', '#479776', 'c', 'm', 'y']

        # 用于控制绘图更新的标志
        self.updated = False

    def update_plot(self, data):
        self.updated = True
        self.data_dict = data
        self.plot_widget.clear()
        self.plot_data()
        # 添加基准线
        self.add_baseline()

    def add_baseline(self):
        baseline = InfiniteLine(pos=0, angle=0, pen=mkPen('r', width=2, style=pg.QtCore.Qt.DashLine))
        self.plot_widget.addItem(baseline)

    def plot_data(self):
        raise NotImplementedError("This method should be implemented by subclasses.")

class ElongationPlotWindow(PlotWindowBase):
    def __init__(self):
        super().__init__("拉伸率变化", "拉伸率")
        self.plot_widget.setYRange(-0.15, 0.1)

    def plot_data(self):
        data_length = len(self.data_dict['bright_l'])
        start_index = max(0, data_length - 30)
        x = range(start_index, data_length)

        name_zh_dic = {'bright_l': "左亮斑", 'bright_m': "中亮斑", 'bright_r': "右亮斑"}

        for idx, (name, elongations) in enumerate(self.data_dict.items()):
            elongations_last_30 = elongations[-30:]
            self.plot_widget.plot(x, [elong - elongations[0] for elong in elongations_last_30], pen=mkPen(self.colors[idx % len(self.colors)], width=5), symbol='o', symbolSize=5, name=name_zh_dic[name])

        # 添加图例
        self.plot_widget.addLegend(offset=(10, 10))

class AreaPlotWindow(PlotWindowBase):
    def __init__(self):
        super().__init__("面积变化", "面积")
        self.plot_widget.setYRange(-1000, 1000)

    def plot_data(self):
        data_length = len(self.data_dict['bright_l'])
        start_index = max(0, data_length - 30)
        x = range(start_index, data_length)

        name_zh_dic = {'bright_l': "左亮斑", 'bright_m': "中亮斑", 'bright_r': "右亮斑"}

        for idx, (name, areas) in enumerate(self.data_dict.items()):
            areas_last_30 = areas[-30:]
            self.plot_widget.plot(x, [area - areas[0] for area in areas_last_30], pen=mkPen(self.colors[idx % len(self.colors)], width=5), symbol='o', symbolSize=5, name=name_zh_dic[name])
        
        # 添加图例
        self.plot_widget.addLegend(offset=(10, 10))

class Std2minPlotWindow(PlotWindowBase):
    def __init__(self):
        super().__init__("标准差/最小值变化", "标准差/最小值")
        self.plot_widget.setYRange(-1, 3)

    def plot_data(self):
        data_length = len(self.data_dict)
        start_index = max(0, data_length - 30)
        x = range(start_index, data_length)

        std2min_data_last_30 = self.data_dict[-30:]
        self.plot_widget.plot(x, [std2min - self.data_dict[0] for std2min in std2min_data_last_30], pen=mkPen('#5092CF', width=5), symbol='o', symbolSize=5, name='暗斑')

        # 添加图例
        self.plot_widget.addLegend(offset=(10, 10))

class BrightnessPlotWindow(PlotWindowBase):
    def __init__(self):
        super().__init__("亮度变化", "亮度")
        self.plot_widget.setYRange(-20, 20)

    def plot_data(self):
        data_length = len(self.data_dict)
        start_index = max(0, data_length - 30)
        x = range(start_index, data_length)

        brightness_last_30 = self.data_dict[-30:]
        self.plot_widget.plot(x, [bright - self.data_dict[0] for bright in brightness_last_30], pen=mkPen('#5092CF', width=5), symbol='o', symbolSize=5, name='亮度')

        # 添加图例
        self.plot_widget.addLegend(offset=(10, 10))

class IntegratedPlotWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("综合图表分析")
        self.setGeometry(100, 100, 900, 600)
        self.setMinimumSize(640, 480)

        # 创建标签页
        self.tabs = QTabWidget(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.tabs)

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
