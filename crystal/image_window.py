import os
from PyQt5.QtWidgets import (QMainWindow, QAction, QHBoxLayout, QVBoxLayout, QLabel, QTextEdit, 
                             QWidget, QPushButton, QSplitter, QDialogButtonBox, QMessageBox, QDialog, QLineEdit, QFormLayout, QHBoxLayout, QFileDialog)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt,QTimer
from .image_processing import spot_detection, compute_std_min_ratio, spot_evaluation, compute_brightness, cut_image
from .utils import get_image_files, convert_image_for_display, update_info, timestamp_to_datetime, split_timestamp_from_filename
import time

class ImageWindow(QMainWindow):
    def __init__(self, plot_window, interval, image_coord, dark_rect):
        super().__init__()
        self.plot_window = plot_window

        self.setWindowTitle("晶体RHEED图像分析系统")
        self.setGeometry(100, 100, 600, 400)

        # 创建菜单栏
        self.menu_bar = self.menuBar()
        file_menu = self.menu_bar.addMenu('文件')
        analysis_menu = self.menu_bar.addMenu('分析')
        window_menu = self.menu_bar.addMenu('视图')
        settings_menu = self.menu_bar.addMenu('设置')
        help_menu = self.menu_bar.addMenu('帮助')

        # 添加菜单项
        open_action = QAction('打开文件夹', self)
        open_action.triggered.connect(self.load_images)
        file_menu.addAction(open_action)

        start_analysis_action = QAction('开始分析', self)
        analysis_menu.addAction(start_analysis_action)
        stop_analysis_action = QAction('停止分析', self)
        analysis_menu.addAction(stop_analysis_action)

        result_win_action = QAction('显示提示窗口', self)
        result_win_action.triggered.connect(self.show_info_dialog)
        window_menu.addAction(result_win_action)
        plot_win_action = QAction('显示图表窗口', self)
        plot_win_action.triggered.connect(self.open_plot_window)
        window_menu.addAction(plot_win_action)

        set_param_action = QAction('设置参数', self)
        set_param_action.triggered.connect(self.open_settings_dialog)
        settings_menu.addAction(set_param_action)
        set_sync_param_action = QAction('设置文件同步', self)
        set_sync_param_action.triggered.connect(self.open_sync_settings_dialog)
        settings_menu.addAction(set_sync_param_action)

        user_guide_action = QAction('使用说明',self)
        help_menu.addAction(user_guide_action)
        about_action = QAction('关于',self)
        help_menu.addAction(about_action)

        main_layout = QHBoxLayout()

        # 左侧布局 - 图像展示区域
        self.imageLabel = QLabel(self)
        self.imageLabel.setScaledContents(True)
        self.imageLabel.setMinimumSize(640, 480)  # 预留图像空间
        self.imageLabel.setStyleSheet("QLabel { background-color: rgb(30, 30, 30); }")
        main_layout.addWidget(self.imageLabel)

        # 右侧布局 - 按钮
        right_layout = QVBoxLayout()
        # 右侧布局 - 按钮
        self.openDirectoryButton = QPushButton("打开文件夹", self)
        self.openDirectoryButton.clicked.connect(self.load_images)

        self.analysisButton = QPushButton("图表分析", self)
        self.analysisButton.clicked.connect(self.open_plot_window)

        self.infoButton = QPushButton("提示窗口", self)
        self.infoButton.clicked.connect(self.show_info_dialog)

        self.settingsButton = QPushButton("参数设置", self)
        self.settingsButton.clicked.connect(self.open_settings_dialog)

        self.syncSettingsButton = QPushButton("文件同步设置", self)
        self.syncSettingsButton.clicked.connect(self.open_sync_settings_dialog)


        self.exitButton = QPushButton("退出", self)
        self.exitButton.clicked.connect(self.close_application)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.openDirectoryButton)
        right_layout.addWidget(self.analysisButton)
        right_layout.addWidget(self.infoButton)
        right_layout.addWidget(self.settingsButton)
        right_layout.addWidget(self.syncSettingsButton)
        right_layout.addWidget(self.exitButton)
        right_layout.addStretch()  # 确保按钮靠上排列

        main_layout.addLayout(right_layout)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # 创建状态栏并存储为属性
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("准备就绪")

        #存放数据
        self.current_folder = None
        self.images = []
        self.current_index = -1
        self.area_data = {'bright_l': [], 'bright_m': [], 'bright_r': []}
        self.elongation_data = {'bright_l': [], 'bright_m': [], 'bright_r': []}
        self.std2min_data = []
        self.brightness_data = []
        self.processed_images = set()

        # 定时器用于定期检查文件夹
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_for_new_images)
        self.timer.start(1000)  

        self.interval = interval
        self.image_coord = image_coord
        self.dark_rect = dark_rect
        self.sync_read_path = r"\\192.168.4.170\test"
        self.sync_save_path = r"./data/test" 

    def open_plot_window(self):
        # 打开图表窗口
        self.plot_window.show()

    def show_info_dialog(self):
        # 显示分析结果窗口
        QMessageBox.information(self, "分析结果", "这里显示分析结果。")

    def open_settings_dialog(self):
        # 打开设置参数对话框的逻辑
        dialog = QDialog(self)
        dialog.setWindowTitle("设置参数")
        layout = QFormLayout()

        # 使用当前参数预填充输入框
        self.image_coord_x1 = QLineEdit(str(self.image_coord[0] if self.image_coord else ""), dialog)
        self.image_coord_y1 = QLineEdit(str(self.image_coord[1] if self.image_coord else ""), dialog)
        self.image_coord_x2 = QLineEdit(str(self.image_coord[2] if self.image_coord else ""), dialog)
        self.image_coord_y2 = QLineEdit(str(self.image_coord[3] if self.image_coord else ""), dialog)

        self.dark_rect_x1 = QLineEdit(str(self.dark_rect[0] if self.dark_rect else ""), dialog)
        self.dark_rect_y1 = QLineEdit(str(self.dark_rect[1] if self.dark_rect else ""), dialog)
        self.dark_rect_x2 = QLineEdit(str(self.dark_rect[2] if self.dark_rect else ""), dialog)
        self.dark_rect_y2 = QLineEdit(str(self.dark_rect[3] if self.dark_rect else ""), dialog)


        # 设置输入提示
        self.image_coord_x1.setPlaceholderText("RHEED图像位置x1")
        self.image_coord_y1.setPlaceholderText("RHEED图像位置y1")
        self.image_coord_x2.setPlaceholderText("RHEED图像位置x2")
        self.image_coord_y2.setPlaceholderText("RHEED图像位置y2")

        self.dark_rect_x1.setPlaceholderText("0-640")
        self.dark_rect_y1.setPlaceholderText("0-480")
        self.dark_rect_x2.setPlaceholderText("0-640")
        self.dark_rect_y2.setPlaceholderText("0-480")

        # 设置焦点跳转
        self.image_coord_x1.returnPressed.connect(lambda: self.image_coord_y1.setFocus())
        self.image_coord_y1.returnPressed.connect(lambda: self.image_coord_x2.setFocus())
        self.image_coord_x2.returnPressed.connect(lambda: self.image_coord_y2.setFocus())
        self.image_coord_y2.returnPressed.connect(lambda: self.dark_rect_x1.setFocus())
        self.dark_rect_x1.returnPressed.connect(lambda: self.dark_rect_y1.setFocus())
        self.dark_rect_y1.returnPressed.connect(lambda: self.dark_rect_x2.setFocus())
        self.dark_rect_x2.returnPressed.connect(lambda: self.dark_rect_y2.setFocus())        

        # 将输入框添加到布局中
        layout.addRow("图像坐标 x1:", self.image_coord_x1)
        layout.addRow("图像坐标 y1:", self.image_coord_y1)
        layout.addRow("图像坐标 x2:", self.image_coord_x2)
        layout.addRow("图像坐标 y2:", self.image_coord_y2)

        layout.addRow("暗斑区域坐标 x1:", self.dark_rect_x1)
        layout.addRow("暗斑区域坐标 y1:", self.dark_rect_y1)
        layout.addRow("暗斑区域坐标 x2:", self.dark_rect_x2)
        layout.addRow("暗斑区域坐标 y2:", self.dark_rect_y2)

        # 添加保存和取消按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        buttons.accepted.connect(dialog.accept)  # 点击保存时接受更改
        buttons.rejected.connect(dialog.reject) # 点击取消时放弃更改
        layout.addWidget(buttons)
        dialog.setLayout(layout)
        result = dialog.exec_()  

        # 如果用户点击保存，则更新坐标信息
        if result == QDialog.Accepted:
            self.image_coord = (self.parse_coordinate(self.image_coord_x1.text()),
                                self.parse_coordinate(self.image_coord_y1.text()),
                                self.parse_coordinate(self.image_coord_x2.text()),
                                self.parse_coordinate(self.image_coord_y2.text()))
            self.dark_rect = (self.parse_coordinate(self.dark_rect_x1.text()),
                              self.parse_coordinate(self.dark_rect_y1.text()),
                              self.parse_coordinate(self.dark_rect_x2.text()),
                              self.parse_coordinate(self.dark_rect_y2.text()))

    def open_sync_settings_dialog(self):
        # 打开文件同步设置对话框的逻辑
        dialog = QDialog(self)
        dialog.setWindowTitle("文件同步设置")
        layout = QFormLayout()

        self.read_path_input = QLineEdit(dialog)
        self.save_path_input = QLineEdit(dialog)

        # 如果已有路径，预填充输入框
        self.read_path_input.setText(self.sync_read_path if self.sync_read_path else "")
        self.save_path_input.setText(self.sync_save_path if self.sync_save_path else "")

        layout.addRow("同步文件读取路径:", self.read_path_input)
        layout.addRow("同步文件保存路径:", self.save_path_input)

        # 添加保存和取消按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)
        result = dialog.exec_()

        # 如果用户点击保存，则更新路径信息
        if result == QDialog.Accepted:
            self.sync_read_path = self.read_path_input.text()
            self.sync_save_path = self.save_path_input.text()


    def parse_coordinate(self, text):
        """
        解析输入的单个坐标文本并转换为整数
        """
        try:
            return int(text.strip())
        except ValueError:
            QMessageBox.warning(self, "格式错误", "请输入有效的整数坐标。")
            return 0

    def close_application(self):
        '''
        退出软件
        '''
        if self.plot_window is not None:
            self.plot_window.close()

        self.close()

    def load_images(self):
        folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        # folder_path = './data/test'
        if not folder_path:
            return

        self.current_folder = folder_path
        self.images = get_image_files(folder_path)

        #清空之前的参数
        self.area_data = {'bright_l': [], 'bright_m': [], 'bright_r': []}
        self.elongation_data = {'bright_l': [], 'bright_m': [], 'bright_r': []}
        self.std2min_data = []
        self.brightness_data = []
        self.current_index = -1  

        if self.images:
            self.display_next_image()

    def display_next_image(self):
        '''
        自动递归更新下一张图片
        '''
        self.current_index += 1
        if self.current_index < len(self.images):
            self.show_image(self.images[self.current_index])
            QTimer.singleShot(self.interval, self.display_next_image)  


    def check_for_new_images(self):
        if not self.current_folder:
            return

        new_images = get_image_files(self.current_folder)
        if not new_images:
            return

        # if len(new_images) > len(self.images):
        #     for new_image in new_images[len(self.images):]:
        #         self.images.append(new_image)
        #         self.show_image(new_image)


        new_unique_images = [img for img in new_images if img not in self.images]

        for new_image in new_unique_images:
            self.images.append(new_image)
            self.show_image(new_image)


    def show_image(self, image_path):
        #展示处理后的图像
        # self.infoBox.clear()

        img = cut_image(image_path, self.image_coord)
        img_with_labels, info = spot_detection(img, self.dark_rect)
        std2min = compute_std_min_ratio(img, self.dark_rect)
        brightness = compute_brightness(img)
        pixmap = convert_image_for_display(img_with_labels)

        image_name = split_timestamp_from_filename(os.path.basename(image_path))
        formatted_time = timestamp_to_datetime(image_name)

        self.status_bar.showMessage(formatted_time)
        self.imageLabel.setPixmap(pixmap)
        self.imageLabel.adjustSize()

        #更新参数
        update_info(info, self.area_data, self.elongation_data)
        self.std2min_data.append(std2min)
        self.brightness_data.append(brightness)

        eval_result = spot_evaluation(image_path, info, self.area_data, self.elongation_data, self.std2min_data)
        # self.infoBox.append(eval_result)

        if image_path not in self.processed_images: 
            self.processed_images.add(image_path)  
            # self.area_window.update_plot(self.area_data)  
            # self.elongation_window.update_plot(self.elongation_data)
            # self.std2min_window.update_plot(self.std2min_data)
            # self.brightness_window.update_plot(self.brightness_data)
            self.plot_window.update_plots(self.elongation_data, self.area_data, self.std2min_data, self.brightness_data)
            # self.hist_window.update_plot([param - self.elongation_data['bright_l'][0] for param in self.elongation_data['bright_l']])
            # self.hist_window.update_plot([param - self.std2min_data[0] for param in self.std2min_data])


