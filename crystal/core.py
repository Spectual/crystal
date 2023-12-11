import sys
from PyQt5.QtWidgets import QApplication
from .image_window import ImageWindow
from .plot_window import AreaPlotWindow, ElongationPlotWindow, Std2minPlotWindow, HistPlotWindow, BrightnessPlotWindow
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--interval', help='time interval (second)', dest='interval', type=float, default=100)
args = parser.parse_known_args()[0]

def run():
    app = QApplication(sys.argv)
    area_plot_window = AreaPlotWindow()
    elongation_plot_window = ElongationPlotWindow()
    std2min_plot_window = Std2minPlotWindow()
    brightness_plot_window = BrightnessPlotWindow()
    hist_plot_window = HistPlotWindow()

    image_window = ImageWindow(area_plot_window, elongation_plot_window, std2min_plot_window, brightness_plot_window, hist_plot_window, args.interval)

    area_plot_window.show()
    elongation_plot_window.show()
    std2min_plot_window.show()
    brightness_plot_window.show()
    hist_plot_window.show()
    image_window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    run()
