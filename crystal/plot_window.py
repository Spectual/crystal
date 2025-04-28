from PyQt5.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QPushButton
from pyqtgraph import PlotWidget, mkPen, InfiniteLine
import pyqtgraph as pg
from pyqtgraph.exporters import ImageExporter
from PyQt5.QtGui import QColor, QFont
import datetime
import os

class PlotWindowBase(QWidget):
    def __init__(self, title, y_axis_label, fileNamePrefix="plot", start_time="2002-09-26_09-20-00"):
        super().__init__()
        self.plot_widget = PlotWidget()
        self.plot_widget.setTitle(title, size='10pt')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setBackground('#EBECEE')  # Set background color to light gray
        self.plot_widget.getAxis('left').setLabel(y_axis_label, color='r', size='10pt')
        self.plot_widget.getAxis('bottom').setStyle(tickFont=QFont("Arial", 10))
        self.plot_widget.getAxis('left').setStyle(tickFont=QFont("Arial", 10))

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.plot_widget)

        # Program start time
        self.start_time = start_time

        # Filename prefix
        self.fileNamePrefix = fileNamePrefix 

        # Dictionary to store data
        self.data_dict = {}

        # Predefined color list
        self.colors = ['#4B89C1', '#DD4444', '#479776', 'c', 'm', 'y']

        # Add save button
        self.saveButton = QPushButton('Save Plot', self)
        self.layout.addWidget(self.saveButton)
        self.saveButton.clicked.connect(self.savePlot)

    def update_plot(self, data):
        self.data_dict = data
        self.plot_widget.clear()
        self.plot_data()
        # Add baseline
        self.add_baseline()

    def add_baseline(self):
        baseline = InfiniteLine(pos=0, angle=0, pen=mkPen('r', width=2, style=pg.QtCore.Qt.DashLine))
        self.plot_widget.addItem(baseline)

    def plot_data(self):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def plot_all_data(self):
        # This method should be implemented in subclasses to plot all data points
        pass

    def savePlot(self):
        # Get program start time
        start_time = self.start_time
        # Define folder name based on start time
        folder_name = os.path.join("plots", start_time)
        
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        
        fileName = os.path.join(folder_name, f"{self.fileNamePrefix}_plot.png")
        
        exporter = ImageExporter(self.plot_widget.plotItem)
        self.plot_widget.clear()
        self.plot_all_data()  # Ensure implemented in subclass
        exporter.export(fileName)
        self.plot_data()  # Restore plot display to show last 30 points

        print(f"Plot saved as: {fileName}")

class AreaPlotWindow(PlotWindowBase):
    def __init__(self, start_time):
        super().__init__("Crystal State Changes", "Crystal State", "area", start_time)
        self.plot_widget.setYRange(-1500, 2000)

    def plot_all_data(self):
        data_length = len(self.data_dict['bright_l'])
        start_index = max(0, data_length - 30)
        x = range(start_index, data_length)

        name_dict = {'bright_l': "Left Bright Spot", 'bright_m': "Middle Bright Spot", 'bright_r': "Right Bright Spot"}

        for idx, (name, areas) in enumerate(self.data_dict.items()):
            x = range(len(areas))
            self.plot_widget.plot(x, [area - areas[0] for area in areas], pen=mkPen(self.colors[idx % len(self.colors)], width=5), symbol='o', symbolSize=5, name=name_dict[name])
        
        self.plot_widget.addLegend(offset=(10, 10))

    def plot_data(self):
        data_length = len(self.data_dict['bright_l'])
        start_index = max(0, data_length - 30)
        x = range(start_index, data_length)

        name_dict = {'bright_l': "Left Bright Spot", 'bright_m': "Middle Bright Spot", 'bright_r': "Right Bright Spot"}
        if len(self.data_dict['bright_l']) <= 30:
            self.plot_widget.setXRange(0, 29, padding=0)
        else:
            self.plot_widget.setXRange(data_length-30, data_length-1)

        for idx, (name, areas) in enumerate(self.data_dict.items()):
            areas_last_30 = areas[-30:]
            self.plot_widget.plot(x, [area - areas[0] for area in areas_last_30], pen=mkPen(self.colors[idx % len(self.colors)], width=5), symbol='o', symbolSize=5, name=name_dict[name])
        
        self.plot_widget.addLegend(offset=(10, 10))

class ElongationPlotWindow(PlotWindowBase):
    def __init__(self, start_time):
        super().__init__("Roundness Coefficient Changes", "Roundness Coefficient", "elongation", start_time)
        self.plot_widget.setYRange(-0.2, 0.3)

    def plot_all_data(self):
        data_length = len(self.data_dict['bright_l'])
        start_index = max(0, data_length - 30)
        x = range(start_index, data_length)

        name_dict = {'bright_l': "Left Bright Spot", 'bright_m': "Middle Bright Spot", 'bright_r': "Right Bright Spot"}
        for idx, (name, elongations) in enumerate(self.data_dict.items()):
            x = range(len(elongations))
            self.plot_widget.plot(x, [elong - elongations[0] for elong in elongations], pen=mkPen(self.colors[idx % len(self.colors)], width=5), symbol='o', symbolSize=5, name=name_dict[name])

        self.plot_widget.addLegend(offset=(10, 10))

    def plot_data(self):
        data_length = len(self.data_dict['bright_l'])
        start_index = max(0, data_length - 30)
        x = range(start_index, data_length)

        name_dict = {'bright_l': "Left Bright Spot", 'bright_m': "Middle Bright Spot", 'bright_r': "Right Bright Spot"}

        for idx, (name, elongations) in enumerate(self.data_dict.items()):
            elongations_last_30 = elongations[-30:]
            self.plot_widget.plot(x, [elong - elongations[0] for elong in elongations_last_30], pen=mkPen(self.colors[idx % len(self.colors)], width=5), symbol='o', symbolSize=5, name=name_dict[name])

        self.plot_widget.addLegend(offset=(10, 10))

class Std2minPlotWindow(PlotWindowBase):
    def __init__(self, start_time):
        super().__init__("Standard Deviation/Min Value Changes", "Std/Min", "std2min", start_time)
        self.plot_widget.setYRange(-30, 30)

    def plot_all_data(self):
        self.plot_widget.setYRange(180, 260)
        data_length = len(self.data_dict)
        start_index = max(0, data_length - 30)
        x = range(len(self.data_dict))

        self.plot_widget.plot(x, [std2min for std2min in self.data_dict], pen=mkPen('#5092CF', width=5), symbol='o', symbolSize=5, name='Dark Spot')
        self.plot_widget.addLegend(offset=(10, 10))

    def plot_data(self):
        data_length = len(self.data_dict)
        start_index = max(0, data_length - 30)
        x = range(start_index, data_length)

        std2min_data_last_30 = self.data_dict[-30:]
        self.plot_widget.plot(x, [std2min - self.data_dict[0] for std2min in std2min_data_last_30], pen=mkPen('#5092CF', width=5), symbol='o', symbolSize=5, name='Dark Spot')
        self.plot_widget.addLegend(offset=(10, 10))

class IntegratedPlotWindow(QWidget):
    def __init__(self, start_time):
        super().__init__()
        self.setWindowTitle("Integrated Plot Analysis")
        self.setGeometry(100, 100, 900, 600)

        # Add charts
        self.area_tab = AreaPlotWindow(start_time=start_time)

        layout = QVBoxLayout(self)
        layout.addWidget(self.area_tab)

    def update_plots(self, elongation_data, area_data, std2min_data):
        self.area_tab.update_plot(area_data)