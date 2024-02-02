import os
import glob
from PyQt5.QtWidgets import (QMainWindow, QAction, QHBoxLayout, QVBoxLayout, QLabel, QTextEdit,
                             QWidget, QTabWidget, QPushButton, QSplitter, QDialogButtonBox, QMessageBox, QDialog,
                             QLineEdit, QFormLayout, QHBoxLayout, QFileDialog, QSizePolicy, QSpacerItem)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt, QTimer, QSize, QEvent
from .image_processing import spot_detection, compute_std_min_ratio, spot_evaluation, compute_brightness, cut_image
from .utils import get_image_files, convert_image_for_display, update_info, timestamp_to_datetime, split_timestamp_from_filename,update_first_info
import time
import platform
import uuid
import numpy as np
system = platform.system()


class ImageWindow(QMainWindow):
    def __init__(self, plot_window, interval, image_coord, dark_rect):
        super().__init__()
        self.plot_window = plot_window
        self.interval = interval
        self.image_coord = image_coord
        self.dark_rect = dark_rect

        self.is_on = True

        # 判断是否是用户选择的标准图片，以便于初始化信息而不需要展示其选择的图片
        self.is_first = False

        #判断是否是第一次加载文件夹
        self.is_first_load = True

        self.recursion_id = uuid.uuid4() 

        # 判断用户是否选择了标准图片，选择则不清空数据
        self.is_selected = False

        self.setWindowTitle("晶体RHEED图像分析系统")
        self.move(100, 100)

        # 创建菜单栏和菜单项
        self.menu_bar = self.menuBar()
        # file_menu = self.menu_bar.addMenu('文件')
        analysis_menu = self.menu_bar.addMenu('分析')
        # window_menu = self.menu_bar.addMenu('视图')
        settings_menu = self.menu_bar.addMenu('设置')
        help_menu = self.menu_bar.addMenu('帮助')

        # open_action = QAction('打开文件夹', self)
        # open_action.triggered.connect(self.load_images)
        # file_menu.addAction(open_action)

        start_analysis_action = QAction('启动分析', self)
        start_analysis_action.triggered.connect(self.load_images)
        analysis_menu.addAction(start_analysis_action)
        stop_analysis_action = QAction('中止分析', self)
        stop_analysis_action.triggered.connect(self.stop_analysis)
        analysis_menu.addAction(stop_analysis_action)
        continue_analysis_action = QAction('继续分析', self)
        continue_analysis_action.triggered.connect(self.continue_analysis)
        analysis_menu.addAction(continue_analysis_action)

        # result_win_action = QAction('显示提示窗口', self)
        # result_win_action.triggered.connect(self.show_info_dialog)
        # window_menu.addAction(result_win_action)
        # plot_win_action = QAction('显示图表窗口', self)
        # plot_win_action.triggered.connect(lambda: self.tabs.setCurrentIndex(1))
        # window_menu.addAction(plot_win_action)

        set_param_action = QAction('设置参数', self)
        set_param_action.triggered.connect(self.open_settings_dialog)
        settings_menu.addAction(set_param_action)
        set_sync_param_action = QAction('设置文件路径', self)
        set_sync_param_action.triggered.connect(self.load_images)
        settings_menu.addAction(set_sync_param_action)
        set_compare_image_action = QAction('设置对比图片路径', self)
        set_compare_image_action.triggered.connect(self.open_compare_settings_dialog)
        settings_menu.addAction(set_compare_image_action)

        user_guide_action = QAction('使用说明', self)
        help_menu.addAction(user_guide_action)
        about_action = QAction('关于', self)
        help_menu.addAction(about_action)

        # 创建图像页面的布局
        self.imageTab = QWidget()
        imageTabLayout = QVBoxLayout(self.imageTab)
        self.imageLabel = QLabel(self)
        self.imageLabel.setScaledContents(False)
        self.imageLabel.setMinimumSize(640, 480)
        self.imageLabel.setStyleSheet("QLabel { background-color: rgb(203, 204, 205); }")
        imageTabLayout.addWidget(self.imageLabel)

        # 设置垂直伸缩策略
        self.imageTab.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.plot_window.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 右侧布局 - 按钮和文本框
        right_layout = QVBoxLayout()

        # 在布局中添加 200 像素的空间
        right_layout.addSpacing(100)

        button_layout = QHBoxLayout()
        # 按钮水平布局
        self.startAnalysisButton = QPushButton("启动分析", self)
        self.startAnalysisButton.clicked.connect(self.load_images)
        self.startAnalysisButton.setMaximumSize(300, 100)  # 设置按钮的固定大小
        # 设置按钮的大小策略，使其在水平和垂直方向上都可以伸缩
        self.startAnalysisButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        button_layout.addWidget(self.startAnalysisButton)

        self.stopAnalysisButton = QPushButton("中止分析", self)
        self.stopAnalysisButton.clicked.connect(self.stop_analysis)
        self.stopAnalysisButton.setMaximumSize(300, 100)
        # 设置按钮的大小策略，使其在水平和垂直方向上都可以伸缩
        self.stopAnalysisButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        button_layout.addWidget(self.stopAnalysisButton)

        self.continueAnalysisButton = QPushButton("继续分析", self)
        self.continueAnalysisButton.clicked.connect(self.continue_analysis)
        self.continueAnalysisButton.setMaximumSize(300, 100)
        # 设置按钮的大小策略，使其在水平和垂直方向上都可以伸缩
        self.continueAnalysisButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        button_layout.addWidget(self.continueAnalysisButton)
        # self.analysisButton = QPushButton("图表分析", self)
        # self.analysisButton.clicked.connect(lambda: self.tabs.setCurrentIndex(1))

        # self.infoButton = QPushButton("提示窗口", self)
        # self.infoButton.clicked.connect(self.show_info_dialog)

        # self.settingsButton = QPushButton("参数设置", self)
        # self.settingsButton.clicked.connect(self.open_settings_dialog)

        # self.syncSettingsButton = QPushButton("文件同步设置", self)
        # self.syncSettingsButton.clicked.connect(self.open_sync_settings_dialog)

        self.exitButton = QPushButton("退出", self)
        self.exitButton.clicked.connect(self.close_application)
        self.exitButton.setMaximumSize(300, 100)
        # 设置按钮的大小策略，使其在水平和垂直方向上都可以伸缩
        self.exitButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        button_layout.addWidget(self.exitButton)

        # 将水平布局添加到垂直布局
        right_layout.addLayout(button_layout)

        # 在布局中添加 200 像素的空间
        right_layout.addSpacing(200)

        # right_layout.addWidget(self.startAnalysisButton)
        # right_layout.addWidget(self.stopAnalysisButton)
        # right_layout.addWidget(self.continueAnalysisButton)
        # right_layout.addWidget(self.analysisButton)
        # right_layout.addWidget(self.infoButton)
        # right_layout.addWidget(self.settingsButton)
        # right_layout.addWidget(self.syncSettingsButton)
        # right_layout.addWidget(self.exitButton)

        # 创建垂直布局用于文本框
        text_layout = QVBoxLayout()

        # 创建实时文本框用于显示分析结果
        self.infoTextBox = QTextEdit(self)
        self.infoTextBox.setReadOnly(True)  # 只读
        self.infoTextBox.setMinimumSize(200, 100)
        # 设置文本框的大小策略，使其能够按比例伸缩
        self.infoTextBox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 设置文本框的字体大小
        font = QFont()
        font.setPointSize(20)  # 设置字体大小
        self.infoTextBox.setFont(font)

        # 添加文本框到垂直布局
        text_layout.addWidget(self.infoTextBox)

        # 将垂直布局添加到右侧布局
        right_layout.addLayout(text_layout)

        # 添加 stretch 到右侧布局，用于调整按钮和文本框的比例
        # right_layout.addStretch(1)

        # 将标签页和按钮布局添加到主布局
        # main_layout = QHBoxLayout()
        # main_layout.addWidget(self.tabs)
        # 添加图像页面和图表页面到主窗口的布局中
        # main_layout.addWidget(self.imageTab)
        # main_layout.addWidget(self.plot_window)
        # main_layout.addLayout(right_layout)

        # 创建垂直布局包含图像页面
        imageLayout = QVBoxLayout()
        imageLayout.addWidget(self.imageTab)

        # 创建垂直布局包含图表页面
        plotLayout = QVBoxLayout()
        plotLayout.addWidget(self.plot_window)

        vertical_layout = QVBoxLayout()
        vertical_layout.addWidget(self.imageTab)
        vertical_layout.addWidget(self.plot_window)

        # 创建水平布局包含垂直布局和right_layout
        main_layout = QHBoxLayout()
        main_layout.addLayout(vertical_layout)
        main_layout.addLayout(right_layout)

        # 设置中心窗口
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # 创建状态栏
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("准备就绪")

        # 存放数据和定时器代码
        self.current_folder = None
        self.images = []
        self.current_index = -1
        self.area_data = {'bright_l': [], 'bright_m': [], 'bright_r': []}
        self.elongation_data = {'bright_l': [], 'bright_m': [], 'bright_r': []}
        self.std2min_data = []
        self.brightness_data = []
        self.processed_images = set()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_for_new_images)
        self.timer.start(100)

        self.sync_read_path = r"\\192.168.4.170\test"
        self.sync_save_path = r"./data/test"

    def open_plot_window(self):
        # 打开图表窗口
        self.plot_window.show()

    # def show_info_dialog(self):
        # 显示分析结果窗口
        # QMessageBox.information(self, "分析结果", "这里显示分析结果。")

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

        self.interval_t = QLineEdit(str(self.interval / 1000 if self.interval else ""), dialog)


        # 设置输入提示
        self.image_coord_x1.setPlaceholderText("RHEED图像位置x1")
        self.image_coord_y1.setPlaceholderText("RHEED图像位置y1")
        self.image_coord_x2.setPlaceholderText("RHEED图像位置x2")
        self.image_coord_y2.setPlaceholderText("RHEED图像位置y2")

        self.dark_rect_x1.setPlaceholderText("0-640")
        self.dark_rect_y1.setPlaceholderText("0-480")
        self.dark_rect_x2.setPlaceholderText("0-640")
        self.dark_rect_y2.setPlaceholderText("0-480")

        self.interval_t.setPlaceholderText("单位 秒(s)")

        # 设置焦点跳转
        self.image_coord_x1.returnPressed.connect(lambda: self.image_coord_y1.setFocus())
        self.image_coord_y1.returnPressed.connect(lambda: self.image_coord_x2.setFocus())
        self.image_coord_x2.returnPressed.connect(lambda: self.image_coord_y2.setFocus())
        self.image_coord_y2.returnPressed.connect(lambda: self.dark_rect_x1.setFocus())
        self.dark_rect_x1.returnPressed.connect(lambda: self.dark_rect_y1.setFocus())
        self.dark_rect_y1.returnPressed.connect(lambda: self.dark_rect_x2.setFocus())
        self.dark_rect_x2.returnPressed.connect(lambda: self.dark_rect_y2.setFocus()) 
        self.dark_rect_y2.returnPressed.connect(lambda: self.interval_t.setFocus()) 

        # 将输入框添加到布局中
        layout.addRow("图像坐标 x1:", self.image_coord_x1)
        layout.addRow("图像坐标 y1:", self.image_coord_y1)
        layout.addRow("图像坐标 x2:", self.image_coord_x2)
        layout.addRow("图像坐标 y2:", self.image_coord_y2)

        layout.addRow("暗斑区域坐标 x1:", self.dark_rect_x1)
        layout.addRow("暗斑区域坐标 y1:", self.dark_rect_y1)
        layout.addRow("暗斑区域坐标 x2:", self.dark_rect_x2)
        layout.addRow("暗斑区域坐标 y2:", self.dark_rect_y2)

        layout.addRow("更新图片间隔:", self.interval_t)

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
            self.interval = max(10, float(self.interval_t.text()) * 1000)

    def open_sync_settings_dialog(self):
        # 打开文件同步设置对话框的逻辑
        dialog = QDialog(self)
        dialog.setWindowTitle("文件路径设置")
        layout = QFormLayout()

        self.read_path_input = QLineEdit(dialog)
        # self.save_path_input = QLineEdit(dialog)

        # 如果已有路径，预填充输入框
        self.read_path_input.setText(self.current_folder if self.current_folder else "")
        # self.save_path_input.setText(self.sync_save_path if self.sync_save_path else "")

        layout.addRow("文件读取路径:", self.read_path_input)
        # layout.addRow("同步文件保存路径:", self.save_path_input)

        # 添加保存和取消按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)
        result = dialog.exec_()

        # 如果用户点击保存，则更新路径信息
        if result == QDialog.Accepted:
            self.current_folder = self.read_path_input.text()
            # self.sync_save_path = self.save_path_input.text()

    def open_compare_settings_dialog(self):
        # 默认文件夹路径
        folder_path = self.current_folder

        # 打开文件对话框并设置初始目录
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setDirectory(folder_path)

        # 获取用户选择的文件路径列表
        selected_files, _ = file_dialog.getOpenFileNames()

        # 检查是否有选择的文件
        if selected_files:
            self.is_selected = True
            # 获取第一个选择的文件路径
            selected_file_path = selected_files[0]
            # 将绝对路径转换为相对路径
            relative_path = os.path.relpath(selected_file_path)

            image_path = relative_path
            img = cut_image(image_path, self.image_coord)
            img_with_labels, info, blocked = spot_detection(img, self.dark_rect)
            std2min = compute_std_min_ratio(img, self.dark_rect) if not blocked else np.nan
            brightness = compute_brightness(img) if not blocked else np.nan

            # 更新参数
            update_first_info(info, self.area_data, self.elongation_data)
            self.std2min_data.insert(0, std2min)
            self.brightness_data.insert(0, brightness)

            # self.plot_window.update_plots(self.elongation_data, self.area_data, self.std2min_data, self.brightness_data)
        else:
            print("用户取消了选择")

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
        '''
        加载图像文件夹
        初始化参数
        开始递归展示图像
        '''

        # folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        # folder_path = r".\data\73"
        self.images = []
        #如果是第一次加载则按默认路径
        if self.is_first_load:
            if system == "Windows":
                folder_path = r".\data\73"
            if system == "Darwin":
                folder_path = "./data/test"
            # folder_path = "/Volumes/Avocado/crystal/data/test"

        else:
            folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
            if not folder_path:
                return

        self.current_folder = folder_path
        self.images = get_image_files(folder_path)
        self.is_first_load = False

        if not self.is_selected:
            #清空之前的参数
            self.area_data = {'bright_l': [], 'bright_m': [], 'bright_r': []}
            self.elongation_data = {'bright_l': [], 'bright_m': [], 'bright_r': []}
            self.std2min_data = []
            self.brightness_data = []
            self.current_index = -1

        # if self.images:
        self.recursion_id = uuid.uuid4()  # 开始新的图片加载时更新标识符
        self.display_next_image(self.recursion_id)  # 传递当前标识符

    def display_next_image(self, current_id):
        '''
        自动递归更新下一张图片
        '''
        # 检查是否还在当前递归序列中
        if current_id != self.recursion_id:
            return  # 如果不是，停止当前的递归调用

        if self.is_on == True:
            if self.current_index < len(self.images) - 1:
                self.current_index += 1
                self.show_image(self.images[self.current_index])
                # QTimer.singleShot(self.interval, self.display_next_image)

        QTimer.singleShot(self.interval, lambda:self.display_next_image(current_id))

    def stop_analysis(self):
        self.is_on = False
        self.status_bar.showMessage("已中止")

    def continue_analysis(self):
        self.is_on = True

    def check_for_new_images(self):
        '''
        检查是否出现新的图像并添加
        '''
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
            # self.show_image(new_image)

    def show_image(self, image_path):
        #展示处理后的图像
        img = cut_image(image_path, self.image_coord)
        img_with_labels, info, blocked = spot_detection(img, self.dark_rect)
        std2min = compute_std_min_ratio(img, self.dark_rect) if not blocked else np.nan
        brightness = compute_brightness(img) if not blocked else np.nan
        # print(brightness)

        pixmap = convert_image_for_display(img_with_labels)

        image_name = split_timestamp_from_filename(os.path.basename(image_path))
        formatted_time = timestamp_to_datetime(image_name)

        if not blocked:
            self.status_bar.showMessage("拍摄时间:"+formatted_time)
        else:
            self.status_bar.showMessage("图像被窗口遮挡")

        self.imageLabel.setPixmap(pixmap.scaled(self.imageLabel.size(), aspectRatioMode=Qt.KeepAspectRatio))
        self.imageLabel.adjustSize()

        scaled_pixmap = pixmap.scaled(self.imageLabel.size(), aspectRatioMode=Qt.KeepAspectRatio)
        self.imageLabel.setPixmap(scaled_pixmap)

        # 获取图像居中放置的位置
        x_pos = (self.imageLabel.width() - scaled_pixmap.width()) // 2
        y_pos = (self.imageLabel.height() - scaled_pixmap.height()) // 2

        # 设置图像的位置
        self.imageLabel.setAlignment(Qt.AlignCenter)
        self.imageLabel.setGeometry(x_pos, y_pos, scaled_pixmap.width(), scaled_pixmap.height())

        #更新参数
        update_info(info, self.area_data, self.elongation_data)
        self.std2min_data.append(std2min)
        self.brightness_data.append(brightness)
        #分析参数
        eval_result = spot_evaluation(image_path, info, self.area_data, self.elongation_data, self.std2min_data, blocked)
        if eval_result:
            self.infoTextBox.append(eval_result)

        if image_path not in self.processed_images: 
            self.processed_images.add(image_path)  
            self.plot_window.update_plots(self.elongation_data, self.area_data, self.std2min_data, self.brightness_data)
