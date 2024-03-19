import sys
import platform
from PyQt5.QtWidgets import QApplication, QSplashScreen, QMainWindow
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer
from .image_window import ImageWindow
from .plot_window import AreaPlotWindow, ElongationPlotWindow, Std2minPlotWindow, BrightnessPlotWindow, IntegratedPlotWindow
import argparse
import time
import qdarkstyle

sys.setrecursionlimit(10**5)  # 设置递归最大深度 10的5次方

system = platform.system()

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--interval', help='time interval (second)', dest='interval', type=float, default=1000)
parser.add_argument('-a', '--image-area', nargs=4, help='image coord', dest='image_coord', type=int, default=(960, 145, 1430, 495))
parser.add_argument('-d', '--dark-rect', nargs=4, help='dark area coord', dest='dark_rect', type=int, default=(204,60,204+330,60+74))

args = parser.parse_known_args()[0]

def run():
    app = QApplication(sys.argv)
    # area_plot_window = AreaPlotWindow()
    # elongation_plot_window = ElongationPlotWindow()
    # std2min_plot_window = Std2minPlotWindow()
    # brightness_plot_window = BrightnessPlotWindow()
    plot_window = IntegratedPlotWindow()
    # hist_plot_window = HistPlotWindow()

    image_window = ImageWindow(plot_window, args.interval, args.image_coord, args.dark_rect)

    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))
    # 创建并显示启动界面

    # 根据操作系统选择图片路径
    if system == "Darwin":
        splash_pix = QPixmap("./imgs/loading.jpg")  
    if system == "Windows":
        splash_pix = QPixmap(r".\imgs\loading.png")
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
    splash.showMessage("加载中...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
    splash.show()

    # 允许处理事件
    app.processEvents()

    # 使用定时器来模拟主窗口加载时间
    # QTimer.singleShot(3000, lambda: (splash.close(), plot_window.show(),  image_window.show()))
    time.sleep(3)

    splash.close()
    # plot_window.show()
    image_window.showMaximized()

    sys.exit(app.exec_())

if __name__ == "__main__":
    run()
