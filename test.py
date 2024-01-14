# import sys
# from PyQt5.QtWidgets import (
#     QApplication, QMainWindow, QAction, QMenuBar, QLabel, QStatusBar, 
#     QWidget, QVBoxLayout, QPushButton, QTextEdit, QFileDialog, QToolBar
# )

# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.title = "RHEED图像智能分析系统"
#         self.initUI()

#     def initUI(self):
#         self.setWindowTitle(self.title)
#         self.setGeometry(100, 100, 800, 600)

#         # 创建菜单栏
#         self.menu_bar = self.menuBar()
#         file_menu = self.menu_bar.addMenu('文件')
#         analysis_menu = self.menu_bar.addMenu('分析')
#         settings_menu = self.menu_bar.addMenu('设置')
#         help_menu = self.menu_bar.addMenu('帮助')

#         # 添加菜单项
#         open_action = QAction('打开图像', self)
#         open_action.triggered.connect(self.openImage)
#         file_menu.addAction(open_action)

#         start_analysis_action = QAction('开始分析', self)
#         analysis_menu.addAction(start_analysis_action)

#         # 创建工具栏
#         self.toolbar = QToolBar("My main toolbar")
#         self.addToolBar(self.toolbar)
#         self.toolbar.addAction(open_action)
#         self.toolbar.addAction(start_analysis_action)

#         # 创建中心窗口
#         central_widget = QWidget()
#         self.setCentralWidget(central_widget)

#         # 垂直布局
#         layout = QVBoxLayout(central_widget)

#         # 图像展示区域
#         self.image_label = QLabel("图像展示区域")
#         layout.addWidget(self.image_label)

#         # 结果展示区域
#         self.results_text = QTextEdit("分析结果")
#         layout.addWidget(self.results_text)

#         # 状态栏
#         self.status_bar = QStatusBar()
#         self.setStatusBar(self.status_bar)

#     def openImage(self):
#         options = QFileDialog.Options()
#         file_name, _ = QFileDialog.getOpenFileName(self, "打开图像", "", "All Files (*);;Image Files (*.png;*.jpg;*.jpeg;*.bmp)", options=options)
#         if file_name:
#             self.image_label.setText(f"选中的文件：{file_name}")
#             self.status_bar.showMessage(f"已加载图像: {file_name}")

# # 主程序入口
# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     mainWin = MainWindow()
#     mainWin.show()
#     sys.exit(app.exec_())

import sys
from PyQt5.QtWidgets import QApplication, QSplashScreen, QMainWindow
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("我的应用程序")
        # 初始化主窗口的其他部分...

# 主程序入口
if __name__ == '__main__':
    app = QApplication(sys.argv)

    # 创建并显示启动界面
    splash_pix = QPixmap("/Users/spectual/Downloads/book.jpg")  # 替换为您的图片路径
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
    splash.showMessage("加载中...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
    splash.show()

    # 允许处理事件
    app.processEvents()

    # 创建主窗口
    main_win = MainWindow()

    # 使用定时器来模拟主窗口加载时间
    QTimer.singleShot(3000, lambda: (splash.close(), main_win.show()))  # 3秒后关闭启动界面并显示主窗口

    sys.exit(app.exec_())
