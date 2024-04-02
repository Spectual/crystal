from PyQt5.QtWidgets import (QMainWindow, QAction, QGridLayout, QHBoxLayout, QVBoxLayout, QGroupBox, QLabel, QSlider,
                             QTextEdit, QTextBrowser, QWidget, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
                             QSplitter, QDialogButtonBox, QMessageBox, QDialog, QLineEdit, QFormLayout, QFileDialog,
                             QSizePolicy, QSpacerItem, QComboBox, QDateTimeEdit, QListWidget)
from PyQt5.QtGui import QPixmap, QFont, QBrush, QColor
from PyQt5.QtCore import Qt, QTimer, QSize, QEvent, QDateTime, QDate, QUrl, QThread, pyqtSignal, QSettings
from .plot_window import IntegratedPlotWindow
from .image_processing import spot_detection, compute_std_min_ratio, spot_evaluation, cut_image
from .utils import get_image_files, convert_image_for_display, update_info, timestamp_to_datetime, split_timestamp_from_filename, update_first_info, init_data_file, init_log_file, record_data, record_log
import numpy as np
import datetime
import platform
import chardet
import shutil
import glob
import time
import uuid
import json
import csv
import cv2
import os


system = platform.system()
deleted_files = set()


class ImageWindow(QMainWindow):
    def __init__(self, interval):
        super().__init__()

        #程序启动时间
        self.start_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.plot_window = IntegratedPlotWindow(self.start_time)

        # 获取项目目录的路径
        project_dir = os.path.dirname(os.path.abspath(__file__))
        last_account_settings_path = os.path.join(project_dir, 'last_account.ini')
        self.settings_last_account = QSettings(last_account_settings_path, QSettings.IniFormat)
        last_used_username = self.settings_last_account.value('username')
        # print(last_used_username)

        self.is_on = True

        # 判断是否是用户选择的标准图片，以便于初始化信息而不需要展示其选择的图片
        self.is_first = False

        # 判断是否是第一次加载文件夹
        self.is_first_load = True

        self.recursion_id = uuid.uuid4()

        # 判断用户是否选择了标准图片，选择则不清空数据
        self.is_selected = False

        # 无异常计数器
        self.no_exception_count = 0

        # 标准图像路径初始化
        self.std_img_path = os.path.join(os.getcwd(), 'imgs', 'standard.png')

        # 未被遮挡的图像初始化
        self.not_blocked_img = self.std_img_path


        # 正在处理的图像变量，存储为图像而非路径，初始化为黑色图像
        self.last_readable_img = cv2.imread(self.std_img_path)

        self.setWindowTitle("IBAD晶体生长过程分析系统")
        # self.setWindowTitle("RHEED晶体图像分析系统")
        self.move(100, 100)

        # 同步线程
        self.sync_thread = None

        # 创建菜单栏和菜单项
        self.menu_bar = self.menuBar()
        # file_menu = self.menu_bar.addMenu('文件')
        analysis_menu = self.menu_bar.addMenu('分析')
        # window_menu = self.menu_bar.addMenu('视图')
        settings_menu = self.menu_bar.addMenu('设置')
        help_menu = self.menu_bar.addMenu('帮助')
        statistic_menu = self.menu_bar.addMenu('统计')
        import_menu = self.menu_bar.addMenu('同步')

        start_analysis_action = QAction('启动分析', self)
        start_analysis_action.triggered.connect(self.load_images)
        analysis_menu.addAction(start_analysis_action)
        stop_analysis_action = QAction('中止分析', self)
        stop_analysis_action.triggered.connect(self.stop_analysis)
        analysis_menu.addAction(stop_analysis_action)
        continue_analysis_action = QAction('继续分析', self)
        continue_analysis_action.triggered.connect(self.continue_analysis)
        analysis_menu.addAction(continue_analysis_action)

        set_param_action = QAction('设置参数', self)
        set_param_action.triggered.connect(self.open_settings_dialog)
        settings_menu.addAction(set_param_action)
        set_sync_param_action = QAction('设置文件路径', self)
        set_sync_param_action.triggered.connect(self.load_images)
        settings_menu.addAction(set_sync_param_action)
        set_compare_image_action = QAction('设置对比图像路径', self)
        set_compare_image_action.triggered.connect(self.open_compare_settings_dialog)
        settings_menu.addAction(set_compare_image_action)

        user_guide_action = QAction('使用说明', self)
        user_guide_action.triggered.connect(self.open_user_guide_dialog)
        help_menu.addAction(user_guide_action)
        about_action = QAction('关于', self)
        about_action.triggered.connect(self.open_about_dialog)
        help_menu.addAction(about_action)

        viewStatisticsAction = QAction('查看统计', self)
        viewStatisticsAction.triggered.connect(self.open_statistics_dialog)
        statistic_menu.addAction(viewStatisticsAction)

        syncImagesAction = QAction('同步图像', self)
        syncImagesAction.triggered.connect(self.open_sync_settings_dialog)
        import_menu.addAction(syncImagesAction)

        stopSyncAction = QAction('停止同步', self)
        stopSyncAction.triggered.connect(self.stop_sync_images)
        import_menu.addAction(stopSyncAction)

        self.imageLabel = QLabel(self)
        self.imageLabel.setScaledContents(False)
        self.imageLabel.setMinimumSize(444, 333)
        self.imageLabel.setStyleSheet("""
            QLabel {
              background-color: #19232D; /* 深蓝色背景 */
              color: #DFE1E2; /* 浅灰色文字 */
              border-radius: 4px; /* 边角圆润度 */
              border: 1px solid #455364; /* 深灰色边框 */
            }
            """)

        # 创建两列的表格
        self.infoTable = QTableWidget(0, 2)  # 初始化为0行2列
        self.infoTable.setHorizontalHeaderLabels(['时间', '提示'])
        # self.infoTable.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.infoTable.setMinimumSize(200, 100)
        self.infoTable.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.infoTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.infoTable.verticalHeader().hide()
        font = QFont()
        font.setPointSize(20)
        self.infoTable.setFont(font)

        # 使用 QSplitter 替换原来的 QHBoxLayout
        horizontal_splitter_top = QSplitter(Qt.Horizontal)
        horizontal_splitter_top.addWidget(self.imageLabel)
        horizontal_splitter_top.addWidget(self.infoTable)

        # 按钮的垂直布局
        vertical_layout_buttons = QVBoxLayout()
        self.startAnalysisButton = QPushButton("启动分析", self)
        self.startAnalysisButton.clicked.connect(self.load_images)
        self.startAnalysisButton.setMaximumSize(200, 50)
        self.startAnalysisButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        vertical_layout_buttons.addWidget(self.startAnalysisButton)

        self.stopAnalysisButton = QPushButton("中止分析", self)
        self.stopAnalysisButton.clicked.connect(self.stop_analysis)
        self.stopAnalysisButton.setMaximumSize(200, 50)
        self.stopAnalysisButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        vertical_layout_buttons.addWidget(self.stopAnalysisButton)

        self.continueAnalysisButton = QPushButton("继续分析", self)
        self.continueAnalysisButton.clicked.connect(self.continue_analysis)
        self.continueAnalysisButton.setMaximumSize(200, 50)
        self.continueAnalysisButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        vertical_layout_buttons.addWidget(self.continueAnalysisButton)

        self.exitButton = QPushButton("退出", self)
        self.exitButton.clicked.connect(self.close_application)
        self.exitButton.setMaximumSize(200, 50)
        self.exitButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        vertical_layout_buttons.addWidget(self.exitButton)

        # 创建主要的水平布局，包含 QSplitter 和按钮的垂直布局
        main_horizontal_layout = QHBoxLayout()
        main_horizontal_layout.addWidget(horizontal_splitter_top)
        main_horizontal_layout.addLayout(vertical_layout_buttons)

        # 创建主要的垂直布局，上方为main_horizontal_layout，下方为图表组件
        main_vertical_layout = QVBoxLayout()
        main_vertical_layout.addLayout(main_horizontal_layout, 1)
        main_vertical_layout.addWidget(self.plot_window, 1)  # 假设你的图表组件是self.plot_window

        # 设置中心窗口布局
        central_widget = QWidget()
        central_widget.setLayout(main_vertical_layout)
        self.setCentralWidget(central_widget)

        # 创建状态栏
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("准备就绪")

        # 存放参数数据和文件路径
        self.current_folder = None
        self.current_index = -1
        self.images = []
        self.area_data = {'bright_l': [], 'bright_m': [], 'bright_r': []}
        self.elongation_data = {'bright_l': [], 'bright_m': [], 'bright_r': []}
        self.std2min_data = []
        self.processed_images = []

        # 操作员名称初始化
        self.user_name = "admin"

        # 数据表格文件初始化
        self.data_file = os.path.join(os.getcwd(), "params", (self.start_time + ".csv"))
        init_data_file(self.data_file)

        # 日志表格文件初始化
        self.log_file = os.path.join(os.getcwd(), "logs", (self.start_time + ".csv"))
        init_log_file(self.log_file)

        #参数初始化
        settings = self.load_default_settings()
        self.interval = settings["interval"]
        self.image_coord = settings["image_coord"]
        self.dark_rect = settings["dark_rect"]
        self.thresholds = settings["thresholds"]

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_for_new_images)
        self.timer.start(1000)

        self.sync_read_path = r"\\192.168.4.170\test"
        self.sync_save_path = r"data\test"

        record_log(self.log_file, self.user_name, "系统事件", "系统启动")

    def open_plot_window(self):
        # 打开图表窗口
        self.plot_window.show()

    def load_default_settings(self):
        with open('config.json', 'r') as file:
            settings = json.load(file)
            return settings

    def open_settings_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("设置参数")
        main_layout = QVBoxLayout(dialog)  # 主布局

        # 图像处理参数设置
        image_processing_group = QGroupBox("图像处理参数")
        image_processing_layout = QFormLayout()
        # 创建并添加图像处理参数控件
        self.image_coord_x1 = QLineEdit(str(self.image_coord[0] if self.image_coord else ""))
        self.image_coord_y1 = QLineEdit(str(self.image_coord[1] if self.image_coord else ""))
        self.image_coord_x2 = QLineEdit(str(self.image_coord[2] if self.image_coord else ""))
        self.image_coord_y2 = QLineEdit(str(self.image_coord[3] if self.image_coord else ""))
        self.dark_rect_x1 = QLineEdit(str(self.dark_rect[0] if self.dark_rect else ""))
        self.dark_rect_y1 = QLineEdit(str(self.dark_rect[1] if self.dark_rect else ""))
        self.dark_rect_x2 = QLineEdit(str(self.dark_rect[2] if self.dark_rect else ""))
        self.dark_rect_y2 = QLineEdit(str(self.dark_rect[3] if self.dark_rect else ""))
        # 添加到布局
        image_processing_layout.addRow("图像坐标 x1:", self.image_coord_x1)
        image_processing_layout.addRow("图像坐标 y1:", self.image_coord_y1)
        image_processing_layout.addRow("图像坐标 x2:", self.image_coord_x2)
        image_processing_layout.addRow("图像坐标 y2:", self.image_coord_y2)
        image_processing_layout.addRow("暗斑区域坐标 x1:", self.dark_rect_x1)
        image_processing_layout.addRow("暗斑区域坐标 y1:", self.dark_rect_y1)
        image_processing_layout.addRow("暗斑区域坐标 x2:", self.dark_rect_x2)
        image_processing_layout.addRow("暗斑区域坐标 y2:", self.dark_rect_y2)
        image_processing_group.setLayout(image_processing_layout)

        # 更新设置
        update_settings_group = QGroupBox("更新设置")
        update_settings_layout = QFormLayout()
        self.interval_t = QLineEdit(str(self.interval / 1000 if self.interval else ""))
        update_settings_layout.addRow("更新图片间隔(秒):", self.interval_t)
        update_settings_group.setLayout(update_settings_layout)

        # 阈值设置
        threshold_settings_group = QGroupBox("阈值设置")
        threshold_settings_layout = QGridLayout()

        # 创建并添加阈值设置控件
        self.no_exception_count_threshold_widgets = self.create_threshold_slider(
            default_value=30, value=self.thresholds['no_exception_count_threshold'], min_value=1, max_value=100,
            title="无异常提示阈值:", factor=1)

        self.elongation_upper_threshold_widgets = self.create_threshold_slider(
            default_value=1, value=self.thresholds['elongation_upper_threshold'], min_value=0, max_value=2,
            title="亮斑近圆系数 上阈值:", factor=20)
        
        self.elongation_lower_threshold_widgets = self.create_threshold_slider(
            default_value=0, value=self.thresholds['elongation_lower_threshold'], min_value=-2, max_value=0,
            title="亮斑近圆系数 下阈值:", factor=20)

        self.area_upper_threshold_widgets = self.create_threshold_slider(
            default_value=800, value=self.thresholds['area_upper_threshold'], min_value=0, max_value=3000,
            title="亮斑面积 上阈值:")

        self.area_lower_threshold_widgets = self.create_threshold_slider(
            default_value=-800, value=self.thresholds['area_lower_threshold'], min_value=-3000, max_value=0,
            title="亮斑面积 下阈值:")

        self.std_min_upper_threshold_widgets = self.create_threshold_slider(
            default_value=50, value=self.thresholds['std_min_upper_threshold'], min_value=0, max_value=200,
            title="暗斑色差 上阈值:")

        self.std_min_lower_threshold_widgets = self.create_threshold_slider(
            default_value=-50, value=self.thresholds['std_min_lower_threshold'], min_value=-200, max_value=0,
            title="暗斑色差 下阈值:")

        threshold_settings_layout.addWidget(self.elongation_upper_threshold_widgets[0], 0, 0)
        threshold_settings_layout.addWidget(self.elongation_upper_threshold_widgets[1], 0, 1)
        threshold_settings_layout.addWidget(self.elongation_upper_threshold_widgets[2], 0, 2)

        threshold_settings_layout.addWidget(self.elongation_lower_threshold_widgets[0], 1, 0)
        threshold_settings_layout.addWidget(self.elongation_lower_threshold_widgets[1], 1, 1)
        threshold_settings_layout.addWidget(self.elongation_lower_threshold_widgets[2], 1, 2)

        threshold_settings_layout.addWidget(self.area_upper_threshold_widgets[0], 2, 0)
        threshold_settings_layout.addWidget(self.area_upper_threshold_widgets[1], 2, 1)
        threshold_settings_layout.addWidget(self.area_upper_threshold_widgets[2], 2, 2)

        threshold_settings_layout.addWidget(self.area_lower_threshold_widgets[0], 3, 0)
        threshold_settings_layout.addWidget(self.area_lower_threshold_widgets[1], 3, 1)
        threshold_settings_layout.addWidget(self.area_lower_threshold_widgets[2], 3, 2)

        threshold_settings_layout.addWidget(self.std_min_upper_threshold_widgets[0], 4, 0)
        threshold_settings_layout.addWidget(self.std_min_upper_threshold_widgets[1], 4, 1)
        threshold_settings_layout.addWidget(self.std_min_upper_threshold_widgets[2], 4, 2)

        threshold_settings_layout.addWidget(self.std_min_lower_threshold_widgets[0], 5, 0)
        threshold_settings_layout.addWidget(self.std_min_lower_threshold_widgets[1], 5, 1)
        threshold_settings_layout.addWidget(self.std_min_lower_threshold_widgets[2], 5, 2)

        threshold_settings_layout.addWidget(self.no_exception_count_threshold_widgets[0], 6,0)
        threshold_settings_layout.addWidget(self.no_exception_count_threshold_widgets[1], 6,1)
        threshold_settings_layout.addWidget(self.no_exception_count_threshold_widgets[2], 6,2)


        # threshold_settings_layout.addWidget(self.elongation_upper_threshold_slider, 0, 1)
        # threshold_settings_layout.addWidget(upper_button, 0, 2)



        threshold_settings_group.setLayout(threshold_settings_layout)

        # 将所有分组添加到主布局
        main_layout.addWidget(image_processing_group)
        main_layout.addWidget(update_settings_group)
        main_layout.addWidget(threshold_settings_group)

        # 添加自定义的保存、取消和恢复默认按钮
        buttons = QDialogButtonBox()
        save_button = buttons.addButton("保存", QDialogButtonBox.AcceptRole)
        cancel_button = buttons.addButton("取消", QDialogButtonBox.RejectRole)
        # 添加恢复默认按钮
        reset_button = buttons.addButton("默认", QDialogButtonBox.ResetRole)
        buttons.accepted.connect(dialog.accept)  # 点击保存时接受更改
        buttons.rejected.connect(dialog.reject)  # 点击取消时放弃更改
        # 点击恢复默认时的操作
        reset_button.clicked.connect(self.reset_defaults)
        main_layout.addWidget(buttons)

        dialog.setLayout(main_layout)
        result = dialog.exec_()

        if result == QDialog.Accepted:
            self.update_settings_from_dialog()

    def create_threshold_slider(self, default_value, min_value, max_value, title, value=0, factor=1):
        # 创建组件但不再包括默认按钮
        title_label = QLabel(title)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_value * factor, max_value * factor)
        slider.setValue(value * factor)
        value_label = QLabel(str(value))
        value_label.setMinimumWidth(60)
        slider.valueChanged.connect(lambda value: value_label.setText(str(value / factor)))
        return [title_label, slider, value_label] 

    def reset_defaults(self):
        settings = self.load_default_settings()
        self.image_coord_x1.setText(str(settings["image_coord"][0]))
        self.image_coord_y1.setText(str(settings["image_coord"][1]))
        self.image_coord_x2.setText(str(settings["image_coord"][2]))
        self.image_coord_y2.setText(str(settings["image_coord"][3]))
        self.dark_rect_x1.setText(str(settings["dark_rect"][0]))
        self.dark_rect_y1.setText(str(settings["dark_rect"][1]))
        self.dark_rect_x2.setText(str(settings["dark_rect"][2]))
        self.dark_rect_y2.setText(str(settings["dark_rect"][3]))
        self.interval_t.setText(str(settings["interval"] / 1000))

        # 设置阈值滑条的默认值
        thresholds = settings["thresholds"]
        self.elongation_upper_threshold_widgets[1].setValue(thresholds["elongation_upper_threshold"] * 20)
        self.elongation_lower_threshold_widgets[1].setValue(thresholds["elongation_lower_threshold"] * 20)
        self.area_upper_threshold_widgets[1].setValue(thresholds["area_upper_threshold"])
        self.area_lower_threshold_widgets[1].setValue(thresholds["area_lower_threshold"])
        self.std_min_upper_threshold_widgets[1].setValue(thresholds["std_min_upper_threshold"])
        self.std_min_lower_threshold_widgets[1].setValue(thresholds["std_min_lower_threshold"])
        self.no_exception_count_threshold_widgets[1].setValue(thresholds["no_exception_count_threshold"])


    def update_settings_from_dialog(self):
        # 更新图像坐标和暗斑区域坐标
        self.image_coord = (
            int(self.image_coord_x1.text()), int(self.image_coord_y1.text()), int(self.image_coord_x2.text()),
            int(self.image_coord_y2.text()))
        self.dark_rect = (int(self.dark_rect_x1.text()), int(self.dark_rect_y1.text()), int(self.dark_rect_x2.text()),
                          int(self.dark_rect_y2.text()))
        self.interval = max(10, float(self.interval_t.text()) * 1000)
        # 更新阈值
        self.thresholds['elongation_upper_threshold'] = self.elongation_upper_threshold_widgets[1].value() / 20
        self.thresholds['elongation_lower_threshold'] = self.elongation_lower_threshold_widgets[1].value() / 20
        self.thresholds['area_upper_threshold'] = self.area_upper_threshold_widgets[1].value()
        self.thresholds['area_lower_threshold'] = self.area_lower_threshold_widgets[1].value()
        self.thresholds['std_min_upper_threshold'] = self.std_min_upper_threshold_widgets[1].value()
        self.thresholds['std_min_lower_threshold'] = self.std_min_lower_threshold_widgets[1].value()
        self.thresholds['no_exception_count_threshold'] = self.no_exception_count_threshold_widgets[1].value()

    def open_statistics_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("统计分析")
        layout = QVBoxLayout(dialog)

        # CSV 文件选择
        self.fileComboBox = QComboBox()
        layout.addWidget(self.fileComboBox)

        # 时间段选择
        self.startTimeEdit = QDateTimeEdit(QDateTime.currentDateTime())
        self.endTimeEdit = QDateTimeEdit(QDateTime.currentDateTime())
        timeLayout = QHBoxLayout()
        timeLayout.addWidget(QLabel("开始时间:"))
        timeLayout.addWidget(self.startTimeEdit)
        timeLayout.addWidget(QLabel("结束时间:"))
        timeLayout.addWidget(self.endTimeEdit)
        layout.addLayout(timeLayout)

        # 信息类型选择
        self.typeComboBox = QComboBox()
        self.infoComboBox = QComboBox()
        infoTypeLayout = QHBoxLayout()
        infoTypeLayout.addWidget(QLabel("信息类型:"))
        infoTypeLayout.addWidget(self.typeComboBox)
        infoTypeLayout.addWidget(QLabel("信息内容:"))
        infoTypeLayout.addWidget(self.infoComboBox)
        layout.addLayout(infoTypeLayout)

        # 结果显示
        self.resultsList = QListWidget()
        layout.addWidget(self.resultsList)

        # 加载按钮
        loadButton = QPushButton("加载数据")
        loadButton.clicked.connect(self.load_data)
        layout.addWidget(loadButton)

        self.load_csv_files()
        self.fileComboBox.currentTextChanged.connect(self.update_types_and_default_dates)
        self.typeComboBox.currentTextChanged.connect(self.update_info_list)

        dialog.setStyleSheet("QWidget {font-size: 16px}")
        dialog.resize(800, 600)
        dialog.exec_()

    def load_csv_files(self):

        logs_dir = os.path.join(os.getcwd(), 'logs')  # 默认路径
        files = [f for f in os.listdir(logs_dir) if f.endswith('.csv')]
        self.fileComboBox.addItems(sorted(files))
        if files:
            self.update_types_and_default_dates(self.fileComboBox.currentText())
            self.update_info_list()

    def update_types_and_default_dates(self, selected_file):
        # 更新默认的开始时间和结束时间
        try:
            date_time_str = selected_file.split('.')[0]
            default_datetime = datetime.datetime.strptime(date_time_str, '%Y-%m-%d_%H-%M-%S')
            self.startTimeEdit.setDateTime(default_datetime)
            self.endTimeEdit.setDateTime(default_datetime)
        except ValueError:
            # 处理可能的日期时间格式错误
            pass

        # 根据选择的 CSV 文件更新类型下拉框
        selected_file_path = os.path.join(os.getcwd(), 'logs', selected_file)
        with open(selected_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            types = set()
            for row in reader:
                types.add(row['类型'])
            self.typeComboBox.clear()
            self.typeComboBox.addItems(['所有'] + sorted(types))

    def update_info_list(self, selected_type=None):
        if not selected_type:
            selected_type = self.typeComboBox.currentText()

        self.infoComboBox.clear()
        self.infoComboBox.addItem("所有")

        if selected_type == "所有" or not selected_type:
            return

        selected_file = self.fileComboBox.currentText()
        filepath = os.path.join('./logs', selected_file)

        with open(filepath, 'rb') as f:
            raw_data = f.read(4096)
            result = chardet.detect(raw_data)
            file_encoding = result['encoding']

        info_set = set()
        with open(filepath, newline='', encoding=file_encoding) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['类型'] == selected_type:
                    info_set.add(row['信息'])

        # 将找到的信息添加到下拉框中
        self.infoComboBox.addItems(sorted(info_set))

    def load_data(self):
        selected_file = self.fileComboBox.currentText()
        start_time = self.startTimeEdit.dateTime().toPyDateTime()
        end_time = self.endTimeEdit.dateTime().toPyDateTime()
        selected_type = self.typeComboBox.currentText()
        selected_info = self.infoComboBox.currentText()  # 获取选定的信息

        self.resultsList.clear()

        filepath = os.path.join(os.getcwd(), 'logs', selected_file)

        with open(filepath, 'rb') as f:
            raw_data = f.read(4096)
            result = chardet.detect(raw_data)
            file_encoding = result['encoding']

        with open(filepath, newline='', encoding=file_encoding) as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                row_time = datetime.datetime.strptime(row['时间'], '%Y-%m-%d_%H-%M-%S')

                if start_time <= row_time <= end_time and (selected_type == '所有' or row['类型'] == selected_type):
                    # 当选择“所有”信息或信息匹配时，添加记录到列表
                    if selected_info == "所有" or row['信息'] == selected_info:
                        display_text = f"{row['时间']} - {row['操作员']} - {row['类型']} - {row['拍摄时间']} - {row['信息']}"
                        self.resultsList.addItem(display_text)

    def open_sync_settings_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("导入文件路径设置")
        layout = QFormLayout()

        self.read_path_input = QLineEdit(dialog)
        self.save_path_input = QLineEdit(dialog)
        self.sync_interval_input = QLineEdit(dialog)  # 新增行：用户输入同步间隔

        # 添加按钮用于打开文件选择器
        read_path_button = QPushButton("选择路径", dialog)
        save_path_button = QPushButton("选择路径", dialog)

        # 设置按钮点击事件
        read_path_button.clicked.connect(lambda: self.select_path(self.read_path_input))
        save_path_button.clicked.connect(lambda: self.select_path(self.save_path_input))

        self.read_path_input.setText(self.sync_read_path if self.sync_read_path else "")
        self.save_path_input.setText(self.sync_save_path if self.sync_save_path else "")
        self.sync_interval_input.setPlaceholderText("同步间隔（秒）")  # 设置占位符提示

        layout.addRow("文件读取路径:", self.read_path_input)
        layout.addWidget(read_path_button)  # 将按钮添加到布局
        layout.addRow("同步文件保存路径:", self.save_path_input)
        layout.addWidget(save_path_button)  # 将按钮添加到布局
        layout.addRow("同步间隔（秒）:", self.sync_interval_input)  # 新增行：添加间隔输入字段

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)
        result = dialog.exec_()

        if result == QDialog.Accepted:
            self.sync_read_path = self.read_path_input.text()  # 更新同步读取路径
            self.sync_save_path = self.save_path_input.text()  # 更新同步保存路径
            # 尝试将间隔转换为浮点数，如果失败则使用默认值1秒
            try:
                self.sync_interval = float(self.sync_interval_input.text())
            except ValueError:
                self.sync_interval = 1.0
            # 启动复制进程
            self.start_copy_images_process()

    def update_status_bar_right(self, message):
        if not hasattr(self, 'status_right_label'):
            self.status_right_label = QLabel()
            self.status_bar.addPermanentWidget(self.status_right_label)
        self.status_right_label.setText(message)

    def start_copy_images_process(self):
        # 检查并终止已有的同步线程
        if self.sync_thread and self.sync_thread.isRunning():
            self.sync_thread.terminate()
            self.sync_thread.wait()  # 等待线程完全终止

        # 使用self.sync_interval作为间隔
        self.sync_thread = CopyImagesThread(self.sync_read_path, self.sync_save_path, self.sync_interval)
        self.sync_thread.update_signal.connect(self.update_status_bar_right)
        self.sync_thread.start()

    def continue_import_images(self):
        if not self.sync_thread or not self.sync_thread.isRunning():
            # 检查并终止已有的同步线程
            if self.sync_thread and self.sync_thread.isRunning():
                self.sync_thread.terminate()
                self.sync_thread.wait()  # 等待线程完全终止

            # 创建并启动新的同步线程，但这次只复制新图片
            self.sync_thread = CopyImagesThread(self.sync_read_path, self.sync_save_path, self.sync_interval, only_new=True)
            self.sync_thread.update_signal.connect(self.update_status_bar_right)
            self.sync_thread.start()
        else:
            QMessageBox.information(self, "操作无效", "当前已有导入操作正在进行中。")

    def stop_sync_images(self):
        # 停止同步线程
        if self.sync_thread and self.sync_thread.isRunning():
            self.sync_thread.terminate()  # 或者使用更安全的停止方法，如果有的话
            self.sync_thread.wait()  # 等待线程完全停止
            self.update_status_bar_right("同步已停止")  # 更新状态栏信息

    def select_path(self, line_edit):
        # 打开文件选择对话框并将选择的路径设置到对应的输入框
        directory = QFileDialog.getExistingDirectory(self, "选择路径")
        if directory:  # 确保用户选择了路径
            line_edit.setText(directory)

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
            img = cut_image(image_path, self.image_coord, self.last_readable_img)
            img_with_labels, info, blocked = spot_detection(img, self.dark_rect)
            std2min = compute_std_min_ratio(img, self.dark_rect) 

            # 更新参数
            update_first_info(info, self.area_data, self.elongation_data)
            self.std2min_data.insert(0, std2min)

            # self.plot_window.update_plots(self.elongation_data, self.area_data, self.std2min_data, self.brightness_data)
        else:
            print("用户取消了选择")

    def open_about_dialog(self):
        QMessageBox.about(self, "关于", 
                          """<b>IBAD晶体生长过程分析系统</b> v1.1.1.240324_beta<br>
                          东部超导科技（苏州）有限公司<br>
                          南京师范大学人工智能研究院<br>""")

    def open_user_guide_dialog(self):
        user_guide_dialog = QDialog(self)
        user_guide_dialog.setWindowTitle("使用说明")
        user_guide_dialog.resize(500, 600)

        # 创建一个文本浏览器，用于显示使用说明
        user_guide_text_browser = QTextBrowser(user_guide_dialog)
        html_file_path = "user_guide.html"  
        user_guide_text_browser.setSource(QUrl.fromLocalFile(html_file_path))
        user_guide_text_browser.setOpenExternalLinks(True)  # 允许打开外部链接

        # 创建布局并添加控件
        layout = QVBoxLayout()
        layout.addWidget(user_guide_text_browser)
        user_guide_dialog.setLayout(layout)

        user_guide_dialog.exec_()

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
        record_log(self.log_file, self.user_name, "系统事件", "系统关闭")
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
        # 如果是第一次加载则按默认路径
        # if self.is_first_load:
        #     if system == "Windows":
        #         folder_path = r".\data\test"
        #     if system == "Darwin":
        #         # folder_path = "/Volumes/Avocado/crystal/data/2-4"
        #         folder_path = "data/73"

        # else:
        folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if not folder_path:
            return

        record_log(self.log_file, self.user_name, "系统事件", "加载图像文件夹:" + folder_path)
        self.current_folder = folder_path
        self.images = get_image_files(folder_path)
        self.is_first_load = False

        # if not self.is_selected:
        # 清空之前的参数
        self.area_data = {'bright_l': [], 'bright_m': [], 'bright_r': []}
        self.elongation_data = {'bright_l': [], 'bright_m': [], 'bright_r': []}
        self.std2min_data = []
        self.processed_images = []
        self.current_index = -1
        self.last_readable_img = ""

        self.infoTable.setRowCount(0)

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

        QTimer.singleShot(self.interval, lambda: self.display_next_image(current_id))

    def stop_analysis(self):
        self.is_on = False
        self.status_bar.showMessage("已中止")
        record_log(self.log_file, self.user_name, "用户操作", "用户点击中止按钮")

    def continue_analysis(self):
        self.is_on = True
        record_log(self.log_file, self.user_name, "用户操作", "用户点击继续按钮")

    def check_for_new_images(self):
        '''
        检查是否出现新的图像并添加
        '''
        if not self.current_folder:
            return

        new_images = get_image_files(self.current_folder)
        if not new_images:
            return

        new_unique_images = [img for img in new_images if img not in self.images]

        for new_image in new_unique_images:
            self.images.append(new_image)
            # self.show_image(new_image)

    def addRow(self, col1_data, col2_data, isException=True):
        row_position = self.infoTable.rowCount()
        self.infoTable.insertRow(row_position)

        # 根据字体大小设置行高
        row_height = max(self.infoTable.fontMetrics().height() + 50, 20)  # 示例行高
        self.infoTable.setRowHeight(row_position, row_height)

        # 创建 QTableWidgetItem 实例，并设置数据
        item1 = QTableWidgetItem(col1_data)
        item2 = QTableWidgetItem(col2_data)

        # 设置文本对齐方式为水平和竖直居中
        item1.setTextAlignment(Qt.AlignCenter)
        item2.setTextAlignment(Qt.AlignCenter)

        # 如果是异常的情况，设置字体颜色为红色
        if isException:
            redBrush = QBrush(QColor(128, 0, 0))
            item2.setForeground(redBrush)

        else:
            greenBrush = QBrush(QColor(0, 128, 0))
            item2.setForeground(greenBrush)

        # 将单元格项添加到表格
        self.infoTable.setItem(row_position, 0, item1)
        self.infoTable.setItem(row_position, 1, item2)

        # self.infoTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # self.infoTable.horizontalHeader().setStretchLastSection(True)

        # 添加行后滚动到底部
        self.infoTable.scrollToBottom()

    def show_image(self, image_path):
        # 展示处理后的图像
        img = cut_image(image_path, self.image_coord, self.last_readable_img)
        self.last_readable_img = img
        img_with_labels, info, blocked = spot_detection(img, self.dark_rect)
        # 如果遮挡则用最近的正常图像替代,仅临时使用，后续需彻底解决
        if blocked:
            img = cut_image(self.not_blocked_img, self.image_coord, self.last_readable_img)
            img_with_labels, info, blocked = spot_detection(img, self.dark_rect)
            blocked = True

        std2min = compute_std_min_ratio(img, self.dark_rect)

        pixmap = convert_image_for_display(img_with_labels)

        image_name = split_timestamp_from_filename(os.path.basename(image_path))
        formatted_time = timestamp_to_datetime(image_name)

        # 参数数据存入表格
        record_data(self.data_file, image_name, formatted_time, std2min, info)

        # 更新参数
        update_info(info, self.area_data, self.elongation_data)
        self.std2min_data.append(std2min)

        # 状态栏
        if not blocked:
            self.not_blocked_img = image_path  # 保存最新没被遮挡的图像，用于替换后续被遮挡的图像
            self.status_bar.showMessage("拍摄时间:" + formatted_time)
        else:
            self.status_bar.showMessage("图像被窗口遮挡")

        # 图像UI组件
        self.imageLabel.setPixmap(pixmap.scaled(self.imageLabel.size(), aspectRatioMode=Qt.KeepAspectRatio))
        self.imageLabel.adjustSize()

        scaled_pixmap = pixmap.scaled(self.imageLabel.size(), aspectRatioMode=Qt.KeepAspectRatio)
        self.imageLabel.setPixmap(scaled_pixmap)

        self.imageLabel.setAlignment(Qt.AlignCenter)

        # 分析参数
        eval_result = spot_evaluation(image_path, info, self.area_data, self.elongation_data, self.std2min_data,
                                      blocked, self.thresholds)

        # 参数记录
        if eval_result:
            self.addRow(formatted_time, eval_result, isException=True)
            record_log(self.log_file, self.user_name, "图像状态", eval_result, formatted_time)
            self.no_exception_count = 0  # 如果检测到异常，重置计数器
        else:
            self.no_exception_count += 1  # 未检测到异常，增加计数器

        # 如果连续多张图像都没有异常，提示无异常
        if self.no_exception_count >= self.thresholds['no_exception_count_threshold']:
            self.addRow(formatted_time, "无异常", isException=False)
            record_log(self.log_file, self.user_name, "图像状态", "无异常", formatted_time)
            self.no_exception_count = 0  # 重置计数器以便新的计数开始

        if image_path not in self.processed_images:
            self.processed_images.append(image_path)
            self.plot_window.update_plots(self.elongation_data, self.area_data, self.std2min_data)



class CopyImagesThread(QThread):
    update_signal = pyqtSignal(str)  # 用于更新状态信息的信号

    def __init__(self, source_folder, target_folder, interval, only_new=False):
        super().__init__()
        self.source_folder = source_folder
        self.target_folder = target_folder
        self.interval = interval
        self.only_new = only_new

    def run(self):
        global deleted_files
        while True:
            image_files = get_image_files(self.source_folder)
            for image_file in image_files:
                target_file = os.path.join(self.target_folder, os.path.basename(image_file))
                # 如果文件在已删除记录中，则跳过复制
                if target_file in deleted_files or (self.only_new and os.path.exists(target_file)):
                    continue
                try:
                    if not os.path.exists(target_file):
                        shutil.copy2(image_file, target_file)
                        self.update_signal.emit(f"文件 {os.path.basename(image_file)} 已被复制到 {self.target_folder}")

                    else:
                        # 如果文件已存在且不在已删除记录中，仍然跳过复制
                        continue
                    time.sleep(self.interval)
                except Exception as e:  # 使用具体的异常类型替代通用的异常捕获
                    self.update_signal.emit(f"复制文件 {image_file} 时发生错误: {e}")

            # 检查目标文件夹，更新已删除文件记录
            current_target_files = {os.path.join(self.target_folder, f) for f in os.listdir(self.target_folder) if
                                    os.path.isfile(os.path.join(self.target_folder, f))}
            source_files = {os.path.join(self.target_folder, os.path.basename(f)) for f in image_files}
            deleted_files.update(deleted_files.union(source_files) - current_target_files)
