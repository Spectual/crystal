import sys
from PyQt5.QtWidgets import QApplication
from .image_window import ImageWindow
from .plot_window import AreaPlotWindow, ElongationPlotWindow, Std2minPlotWindow

def run():
    app = QApplication(sys.argv)
    area_plot_window = AreaPlotWindow()
    elongation_plot_window = ElongationPlotWindow()
    std2min_plot_window = Std2minPlotWindow()
    image_window = ImageWindow(area_plot_window, elongation_plot_window, std2min_plot_window)

    area_plot_window.show()
    elongation_plot_window.show()
    std2min_plot_window.show()
    image_window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    run()
