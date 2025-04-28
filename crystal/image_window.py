from PyQt5.QtWidgets import (QMainWindow, QAction, QGridLayout, QHBoxLayout, QVBoxLayout, QGroupBox, QLabel, QSlider, QRadioButton, QButtonGroup,
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

        # Program start time
        self.start_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.plot_window = IntegratedPlotWindow(self.start_time)

        # Get project directory path
        project_dir = os.path.dirname(os.path.abspath(__file__))
        last_account_settings_path = os.path.join(project_dir, 'last_account.ini')
        self.settings_last_account = QSettings(last_account_settings_path, QSettings.IniFormat)
        last_used_username = self.settings_last_account.value('username')

        self.is_on = True

        # Flag to determine if a standard image was selected, 
        # to initialize information without showing the image
        self.is_first = False

        # Flag to check if the folder is loaded for the first time
        self.is_first_load = True

        self.recursion_id = uuid.uuid4()

        # Flag to determine whether the user selected a standard image, 
        # if yes, do not clear data
        self.is_selected = False

        # No-exception counter
        self.no_exception_count = 0

        # Initialize standard image path
        self.std_img_path = os.path.join(os.getcwd(), 'imgs', 'standard.png')

        # Initialize non-blocked image
        self.not_blocked_img = self.std_img_path

        # Last readable image (stored as image, not path), initialized with a black image
        self.last_readable_img = cv2.imread(self.std_img_path)

        self.setWindowTitle("IBAD Crystal Growth Process Analysis System")
        self.move(100, 100)

        # Synchronization thread
        self.sync_thread = None

        # Create menu bar and menu items
        self.menu_bar = self.menuBar()
        analysis_menu = self.menu_bar.addMenu('Analysis')
        settings_menu = self.menu_bar.addMenu('Settings')
        help_menu = self.menu_bar.addMenu('Help')
        statistic_menu = self.menu_bar.addMenu('Statistics')
        import_menu = self.menu_bar.addMenu('Sync')

        start_analysis_action = QAction('Start Analysis', self)
        start_analysis_action.triggered.connect(self.load_images)
        analysis_menu.addAction(start_analysis_action)

        stop_analysis_action = QAction('Stop Analysis', self)
        stop_analysis_action.triggered.connect(self.stop_analysis)
        analysis_menu.addAction(stop_analysis_action)

        continue_analysis_action = QAction('Continue Analysis', self)
        continue_analysis_action.triggered.connect(self.continue_analysis)
        analysis_menu.addAction(continue_analysis_action)

        set_param_action = QAction('Set Parameters', self)
        set_param_action.triggered.connect(self.open_settings_dialog)
        settings_menu.addAction(set_param_action)

        set_sync_param_action = QAction('Set File Path', self)
        set_sync_param_action.triggered.connect(self.load_images)
        settings_menu.addAction(set_sync_param_action)

        set_compare_image_action = QAction('Set Comparison Image Path', self)
        set_compare_image_action.triggered.connect(self.open_compare_settings_dialog)
        settings_menu.addAction(set_compare_image_action)

        user_guide_action = QAction('User Guide', self)
        user_guide_action.triggered.connect(self.open_user_guide_dialog)
        help_menu.addAction(user_guide_action)

        about_action = QAction('About', self)
        about_action.triggered.connect(self.open_about_dialog)
        help_menu.addAction(about_action)

        viewStatisticsAction = QAction('View Statistics', self)
        viewStatisticsAction.triggered.connect(self.open_statistics_dialog)
        statistic_menu.addAction(viewStatisticsAction)

        syncImagesAction = QAction('Sync Images', self)
        syncImagesAction.triggered.connect(self.open_sync_settings_dialog)
        import_menu.addAction(syncImagesAction)

        stopSyncAction = QAction('Stop Sync', self)
        stopSyncAction.triggered.connect(self.stop_sync_images)
        import_menu.addAction(stopSyncAction)

        self.imageLabel = QLabel(self)
        self.imageLabel.setScaledContents(False)
        self.imageLabel.setMinimumSize(444, 333)
        self.imageLabel.setStyleSheet("""
            QLabel {
              background-color: #19232D;
              color: #DFE1E2;
              border-radius: 4px;
              border: 1px solid #455364;
            }
        """)

        # Create a table with two columns
        self.infoTable = QTableWidget(0, 2)  # Initialize with 0 rows and 2 columns
        self.infoTable.setHorizontalHeaderLabels(['Time', 'Message'])
        self.infoTable.setMinimumSize(200, 100)
        self.infoTable.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.infoTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.infoTable.verticalHeader().hide()
        font = QFont()
        font.setPointSize(20)
        self.infoTable.setFont(font)

        # Replace original QHBoxLayout with QSplitter
        horizontal_splitter_top = QSplitter(Qt.Horizontal)
        horizontal_splitter_top.addWidget(self.imageLabel)
        horizontal_splitter_top.addWidget(self.infoTable)

        # Vertical layout for buttons
        vertical_layout_buttons = QVBoxLayout()
        self.startAnalysisButton = QPushButton("Start Analysis", self)
        self.startAnalysisButton.clicked.connect(self.load_images)
        self.startAnalysisButton.setMaximumSize(200, 50)
        self.startAnalysisButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        vertical_layout_buttons.addWidget(self.startAnalysisButton)

        self.stopAnalysisButton = QPushButton("Stop Analysis", self)
        self.stopAnalysisButton.clicked.connect(self.stop_analysis)
        self.stopAnalysisButton.setMaximumSize(200, 50)
        self.stopAnalysisButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        vertical_layout_buttons.addWidget(self.stopAnalysisButton)

        self.continueAnalysisButton = QPushButton("Continue Analysis", self)
        self.continueAnalysisButton.clicked.connect(self.continue_analysis)
        self.continueAnalysisButton.setMaximumSize(200, 50)
        self.continueAnalysisButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        vertical_layout_buttons.addWidget(self.continueAnalysisButton)

        self.exitButton = QPushButton("Exit", self)
        self.exitButton.clicked.connect(self.close_application)
        self.exitButton.setMaximumSize(200, 50)
        self.exitButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        vertical_layout_buttons.addWidget(self.exitButton)

        # Main horizontal layout with QSplitter and vertical buttons
        main_horizontal_layout = QHBoxLayout()
        main_horizontal_layout.addWidget(horizontal_splitter_top)
        main_horizontal_layout.addLayout(vertical_layout_buttons)

        # Main vertical layout: upper part is horizontal layout, lower part is the plot window
        main_vertical_layout = QVBoxLayout()
        main_vertical_layout.addLayout(main_horizontal_layout, 1)
        main_vertical_layout.addWidget(self.plot_window, 1)

        # Set the central widget layout
        central_widget = QWidget()
        central_widget.setLayout(main_vertical_layout)
        self.setCentralWidget(central_widget)

        # Create status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

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

        record_log(self.log_file, self.user_name, "System Event", "System Startup")

    def open_plot_window(self):
        # 打开图表窗口
        self.plot_window.show()

    def load_default_settings(self):
        with open('config.json', 'r') as file:
            settings = json.load(file)
            return settings

    def open_settings_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Set Parameters")
        main_layout = QVBoxLayout(dialog)  # Main layout

        # Image Processing Parameter Settings
        image_processing_group = QGroupBox("Image Processing Parameters")
        image_processing_layout = QFormLayout()
        # Create and add image processing parameter controls
        self.image_coord_x1 = QLineEdit(str(self.image_coord[0] if self.image_coord else ""))
        self.image_coord_y1 = QLineEdit(str(self.image_coord[1] if self.image_coord else ""))
        self.image_coord_x2 = QLineEdit(str(self.image_coord[2] if self.image_coord else ""))
        self.image_coord_y2 = QLineEdit(str(self.image_coord[3] if self.image_coord else ""))
        self.dark_rect_x1 = QLineEdit(str(self.dark_rect[0] if self.dark_rect else ""))
        self.dark_rect_y1 = QLineEdit(str(self.dark_rect[1] if self.dark_rect else ""))
        self.dark_rect_x2 = QLineEdit(str(self.dark_rect[2] if self.dark_rect else ""))
        self.dark_rect_y2 = QLineEdit(str(self.dark_rect[3] if self.dark_rect else ""))
        # Add to layout
        image_processing_layout.addRow("Image Coordinate x1:", self.image_coord_x1)
        image_processing_layout.addRow("Image Coordinate y1:", self.image_coord_y1)
        image_processing_layout.addRow("Image Coordinate x2:", self.image_coord_x2)
        image_processing_layout.addRow("Image Coordinate y2:", self.image_coord_y2)
        image_processing_layout.addRow("Dark Spot Area x1:", self.dark_rect_x1)
        image_processing_layout.addRow("Dark Spot Area y1:", self.dark_rect_y1)
        image_processing_layout.addRow("Dark Spot Area x2:", self.dark_rect_x2)
        image_processing_layout.addRow("Dark Spot Area y2:", self.dark_rect_y2)
        image_processing_group.setLayout(image_processing_layout)

        # Update Settings
        update_settings_group = QGroupBox("Update Settings")
        update_settings_layout = QFormLayout()
        self.interval_t = QLineEdit(str(self.interval / 1000 if self.interval else ""))
        update_settings_layout.addRow("Image Update Interval (seconds):", self.interval_t)
        update_settings_group.setLayout(update_settings_layout)

        # Threshold Settings
        threshold_settings_group = QGroupBox("Threshold Settings")
        threshold_settings_layout = QGridLayout()

        self.elongation_upper_threshold_widgets = self.create_threshold_radiobuttons("Bright Spot Roundness Upper Threshold:", value=self.thresholds['elongation_upper_threshold_index'])
        self.elongation_lower_threshold_widgets = self.create_threshold_radiobuttons("Bright Spot Roundness Lower Threshold:", value=self.thresholds['elongation_lower_threshold_index'])
        self.area_upper_threshold_widgets = self.create_threshold_radiobuttons("Bright Spot Area Upper Threshold:", value=self.thresholds['area_upper_threshold_index'])
        self.area_lower_threshold_widgets = self.create_threshold_radiobuttons("Bright Spot Area Lower Threshold:", value=self.thresholds['area_lower_threshold_index'])
        self.std_min_upper_threshold_widgets = self.create_threshold_radiobuttons("Dark Spot Color Difference Upper Threshold:", value=self.thresholds['std_min_upper_threshold_index'])
        self.std_min_lower_threshold_widgets = self.create_threshold_radiobuttons("Dark Spot Color Difference Lower Threshold:", value=self.thresholds['std_min_lower_threshold_index'])
        self.no_exception_count_threshold_widgets = self.create_threshold_radiobuttons("No Exception Prompt Threshold:", value=self.thresholds['no_exception_count_threshold_index'])

        # Add radio button groups to layout
        threshold_settings_layout.addWidget(self.elongation_upper_threshold_widgets[0], 0, 0, 1, 3)
        threshold_settings_layout.addLayout(self.elongation_upper_threshold_widgets[1], 0, 3)
        threshold_settings_layout.addWidget(self.elongation_lower_threshold_widgets[0], 1, 0, 1, 3)
        threshold_settings_layout.addLayout(self.elongation_lower_threshold_widgets[1], 1, 3)
        threshold_settings_layout.addWidget(self.area_upper_threshold_widgets[0], 2, 0, 1, 3)
        threshold_settings_layout.addLayout(self.area_upper_threshold_widgets[1], 2, 3)
        threshold_settings_layout.addWidget(self.area_lower_threshold_widgets[0], 3, 0, 1, 3)
        threshold_settings_layout.addLayout(self.area_lower_threshold_widgets[1], 3, 3)
        threshold_settings_layout.addWidget(self.std_min_upper_threshold_widgets[0], 4, 0, 1, 3)
        threshold_settings_layout.addLayout(self.std_min_upper_threshold_widgets[1], 4, 3)
        threshold_settings_layout.addWidget(self.std_min_lower_threshold_widgets[0], 5, 0, 1, 3)
        threshold_settings_layout.addLayout(self.std_min_lower_threshold_widgets[1], 5, 3)
        threshold_settings_layout.addWidget(self.no_exception_count_threshold_widgets[0], 6, 0, 1, 3)
        threshold_settings_layout.addLayout(self.no_exception_count_threshold_widgets[1], 6, 3)

        threshold_settings_group.setLayout(threshold_settings_layout)

        # Add all groups to main layout
        main_layout.addWidget(image_processing_group)
        main_layout.addWidget(update_settings_group)
        main_layout.addWidget(threshold_settings_group)

        # Add custom Save, Cancel, and Reset to Default buttons
        buttons = QDialogButtonBox()
        save_button = buttons.addButton("Save", QDialogButtonBox.AcceptRole)
        cancel_button = buttons.addButton("Cancel", QDialogButtonBox.RejectRole)
        reset_button = buttons.addButton("Default", QDialogButtonBox.ResetRole)
        buttons.accepted.connect(dialog.accept)  # Save changes on accept
        buttons.rejected.connect(dialog.reject)  # Discard changes on reject
        reset_button.clicked.connect(self.reset_defaults)  # Reset to default settings
        main_layout.addWidget(buttons)

        dialog.setLayout(main_layout)
        result = dialog.exec_()

        if result == QDialog.Accepted:
            self.update_settings_from_dialog()

    def create_threshold_radiobuttons(self, title, value):
        title_label = QLabel(title)
        layout = QHBoxLayout()
        button_group = QButtonGroup(layout)  
        low_button = QRadioButton("low")
        medium_button = QRadioButton("mid")
        high_button = QRadioButton("high")
        
        layout.addWidget(low_button)
        layout.addWidget(medium_button)
        layout.addWidget(high_button)
        
        # 将按钮添加到按钮组，设置ID
        button_group.addButton(low_button, 0)
        button_group.addButton(medium_button, 1)
        button_group.addButton(high_button, 2)
        
        # 连接信号和槽
        # button_group.buttonClicked[int].connect(lambda value, key=setting_key: self.set_threshold_value(key, value))
        button_group.button(value).setChecked(True)

        return title_label, layout, button_group

    def create_threshold_slider(self, min_value, max_value, title, value=0, factor=1):
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
        self.elongation_upper_threshold_widgets[2].button(thresholds['elongation_upper_threshold_index']).setChecked(True)
        self.elongation_lower_threshold_widgets[2].button(thresholds['elongation_lower_threshold_index']).setChecked(True)
        self.area_upper_threshold_widgets[2].button(thresholds['area_upper_threshold_index']).setChecked(True)
        self.area_lower_threshold_widgets[2].button(thresholds['area_lower_threshold_index']).setChecked(True)
        self.std_min_upper_threshold_widgets[2].button(thresholds['std_min_upper_threshold_index']).setChecked(True)
        self.std_min_lower_threshold_widgets[2].button(thresholds['std_min_lower_threshold_index']).setChecked(True)
        self.no_exception_count_threshold_widgets[2].button(thresholds['no_exception_count_threshold_index']).setChecked(True)

    def update_settings_from_dialog(self):
        # 更新图像坐标和暗斑区域坐标
        self.image_coord = (
            int(self.image_coord_x1.text()), int(self.image_coord_y1.text()), int(self.image_coord_x2.text()),
            int(self.image_coord_y2.text()))
        self.dark_rect = (int(self.dark_rect_x1.text()), int(self.dark_rect_y1.text()), int(self.dark_rect_x2.text()),
                          int(self.dark_rect_y2.text()))
        self.interval = max(10, float(self.interval_t.text()) * 1000)
        # 更新阈值
        self.thresholds['elongation_upper_threshold_index'] = self.elongation_upper_threshold_widgets[2].checkedId()
        self.thresholds['area_upper_threshold_index'] = self.area_upper_threshold_widgets[2].checkedId()
        self.thresholds['std_min_upper_threshold_index'] = self.std_min_upper_threshold_widgets[2].checkedId()
        self.thresholds['elongation_lower_threshold_index'] = self.elongation_lower_threshold_widgets[2].checkedId()
        self.thresholds['area_lower_threshold_index'] = self.area_lower_threshold_widgets[2].checkedId()
        self.thresholds['std_min_lower_threshold_index'] = self.std_min_lower_threshold_widgets[2].checkedId()
        self.thresholds['no_exception_count_threshold_index'] = self.no_exception_count_threshold_widgets[2].checkedId()

        self.thresholds['elongation_upper_threshold'] = self.thresholds['elongation_upper_threshold_list'][self.thresholds['elongation_upper_threshold_index']]
        self.thresholds['area_upper_threshold'] = self.thresholds['area_upper_threshold_list'][self.thresholds['area_upper_threshold_index']]
        self.thresholds['std_min_upper_threshold'] = self.thresholds['std_min_upper_threshold_list'][self.thresholds['std_min_upper_threshold_index']]
        self.thresholds['elongation_lower_threshold'] = self.thresholds['elongation_lower_threshold_list'][self.thresholds['elongation_lower_threshold_index']]
        self.thresholds['area_lower_threshold'] = self.thresholds['area_lower_threshold_list'][self.thresholds['area_lower_threshold_index']]
        self.thresholds['std_min_lower_threshold'] = self.thresholds['std_min_lower_threshold_list'][self.thresholds['std_min_lower_threshold_index']]
        self.thresholds['no_exception_count_threshold'] = self.thresholds['no_exception_count_threshold_list'][self.thresholds['no_exception_count_threshold_index']]

    def open_statistics_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Statistical Analysis")
        layout = QVBoxLayout(dialog)

        # CSV File Selection
        self.fileComboBox = QComboBox()
        layout.addWidget(self.fileComboBox)

        # Time Range Selection
        self.startTimeEdit = QDateTimeEdit(QDateTime.currentDateTime())
        self.endTimeEdit = QDateTimeEdit(QDateTime.currentDateTime())
        timeLayout = QHBoxLayout()
        timeLayout.addWidget(QLabel("Start Time:"))
        timeLayout.addWidget(self.startTimeEdit)
        timeLayout.addWidget(QLabel("End Time:"))
        timeLayout.addWidget(self.endTimeEdit)
        layout.addLayout(timeLayout)

        # Information Type Selection
        self.typeComboBox = QComboBox()
        self.infoComboBox = QComboBox()
        infoTypeLayout = QHBoxLayout()
        infoTypeLayout.addWidget(QLabel("Information Type:"))
        infoTypeLayout.addWidget(self.typeComboBox)
        infoTypeLayout.addWidget(QLabel("Information Content:"))
        infoTypeLayout.addWidget(self.infoComboBox)
        layout.addLayout(infoTypeLayout)

        # Results Display
        self.resultsList = QListWidget()
        layout.addWidget(self.resultsList)

        # Load Button
        loadButton = QPushButton("Load Data")
        loadButton.clicked.connect(self.load_data)
        layout.addWidget(loadButton)

        # Load CSV file options and connect signals
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
        # Update default start and end times
        try:
            date_time_str = selected_file.split('.')[0]
            default_datetime = datetime.datetime.strptime(date_time_str, '%Y-%m-%d_%H-%M-%S')
            self.startTimeEdit.setDateTime(default_datetime)
            self.endTimeEdit.setDateTime(default_datetime)
        except ValueError:
            # Handle possible datetime format errors
            pass

        # Update type dropdown based on selected CSV file
        selected_file_path = os.path.join(os.getcwd(), 'logs', selected_file)
        with open(selected_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            types = set()
            for row in reader:
                types.add(row['Type'])  # '类型' -> 'Type'
            self.typeComboBox.clear()
            self.typeComboBox.addItems(['All'] + sorted(types))

    def update_info_list(self, selected_type=None):
        if not selected_type:
            selected_type = self.typeComboBox.currentText()

        self.infoComboBox.clear()
        self.infoComboBox.addItem("All")

        if selected_type == "All" or not selected_type:
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
                if row['Type'] == selected_type:  # '类型' -> 'Type'
                    info_set.add(row['Information'])  # '信息' -> 'Information'

        # Add the found information items into the dropdown
        self.infoComboBox.addItems(sorted(info_set))

    def load_data(self):
        selected_file = self.fileComboBox.currentText()
        start_time = self.startTimeEdit.dateTime().toPyDateTime()
        end_time = self.endTimeEdit.dateTime().toPyDateTime()
        selected_type = self.typeComboBox.currentText()
        selected_info = self.infoComboBox.currentText()  # Get selected information

        self.resultsList.clear()

        filepath = os.path.join(os.getcwd(), 'logs', selected_file)

        with open(filepath, 'rb') as f:
            raw_data = f.read(4096)
            result = chardet.detect(raw_data)
            file_encoding = result['encoding']

        with open(filepath, newline='', encoding=file_encoding) as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                row_time = datetime.datetime.strptime(row['Time'], '%Y-%m-%d_%H-%M-%S')  # '时间' -> 'Time'

                if start_time <= row_time <= end_time and (selected_type == 'All' or row['Type'] == selected_type):
                    # When selecting "All" or matching type, add the record to the list
                    if selected_info == "All" or row['Information'] == selected_info:
                        display_text = f"{row['Time']} - {row['Operator']} - {row['Type']} - {row['Capture Time']} - {row['Information']}"
                        self.resultsList.addItem(display_text)

    def open_sync_settings_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Import File Path Settings")
        layout = QFormLayout()

        self.read_path_input = QLineEdit(dialog)
        self.save_path_input = QLineEdit(dialog)
        self.sync_interval_input = QLineEdit(dialog)  # New: user input for sync interval

        # Add buttons to open file picker
        read_path_button = QPushButton("Select Path", dialog)
        save_path_button = QPushButton("Select Path", dialog)

        # Set button click events
        read_path_button.clicked.connect(lambda: self.select_path(self.read_path_input))
        save_path_button.clicked.connect(lambda: self.select_path(self.save_path_input))

        self.read_path_input.setText(self.sync_read_path if self.sync_read_path else "")
        self.save_path_input.setText(self.sync_save_path if self.sync_save_path else "")
        self.sync_interval_input.setPlaceholderText("Sync Interval (seconds)")  # Set placeholder text

        layout.addRow("File Read Path:", self.read_path_input)
        layout.addWidget(read_path_button)  # Add button to layout
        layout.addRow("Sync File Save Path:", self.save_path_input)
        layout.addWidget(save_path_button)  # Add button to layout
        layout.addRow("Sync Interval (seconds):", self.sync_interval_input)  # New: add sync interval field

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)
        result = dialog.exec_()

        if result == QDialog.Accepted:
            self.sync_read_path = self.read_path_input.text()  # Update read path
            self.sync_save_path = self.save_path_input.text()  # Update save path
            # Try to convert interval to float, fallback to default 1 second
            try:
                self.sync_interval = float(self.sync_interval_input.text())
            except ValueError:
                self.sync_interval = 1.0
            # Start the copy process
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
            # Check and terminate any existing sync thread
            if self.sync_thread and self.sync_thread.isRunning():
                self.sync_thread.terminate()
                self.sync_thread.wait()  # Wait for the thread to fully terminate

            # Create and start a new sync thread, but this time only copy new images
            self.sync_thread = CopyImagesThread(self.sync_read_path, self.sync_save_path, self.sync_interval, only_new=True)
            self.sync_thread.update_signal.connect(self.update_status_bar_right)
            self.sync_thread.start()
        else:
            QMessageBox.information(self, "Operation Invalid", "An import operation is already in progress.")

    def stop_sync_images(self):
        # Stop the sync thread
        if self.sync_thread and self.sync_thread.isRunning():
            self.sync_thread.terminate()  # Or use a safer stop method if available
            self.sync_thread.wait()  # Wait for the thread to fully stop
            self.update_status_bar_right("Sync Stopped")  # Update status bar message

    def select_path(self, line_edit):
        # Open a directory selection dialog and set the selected path to the corresponding input box
        directory = QFileDialog.getExistingDirectory(self, "Select Path")
        if directory:  # Make sure a path was selected
            line_edit.setText(directory)

    def open_compare_settings_dialog(self):
        # Default folder path
        folder_path = self.current_folder

        # Open file dialog with initial directory
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setDirectory(folder_path)

        # Get list of selected file paths
        selected_files, _ = file_dialog.getOpenFileNames()

        # Check if files were selected
        if selected_files:
            self.is_selected = True
            # Get the first selected file path
            selected_file_path = selected_files[0]
            # Convert absolute path to relative path
            relative_path = os.path.relpath(selected_file_path)

            image_path = relative_path
            img = cut_image(image_path, self.image_coord, self.last_readable_img)
            img_with_labels, info, blocked = spot_detection(img, self.dark_rect)
            std2min = compute_std_min_ratio(img, self.dark_rect)

            # Update parameters
            update_first_info(info, self.area_data, self.elongation_data)
            self.std2min_data.insert(0, std2min)

            # self.plot_window.update_plots(self.elongation_data, self.area_data, self.std2min_data, self.brightness_data)
        else:
            print("User canceled the selection.")

    def open_about_dialog(self):
        QMessageBox.about(self, "About", 
                          """<b>IBAD Crystal Growth Process Analysis System</b> v1.1.1.240324_beta<br>
                          Eastern Superconductor Technology (Suzhou) Co., Ltd.<br>
                          Institute of Artificial Intelligence, Nanjing Normal University<br>""")

    def open_user_guide_dialog(self):
        user_guide_dialog = QDialog(self)
        user_guide_dialog.setWindowTitle("User Guide")
        user_guide_dialog.resize(500, 600)

        # Create a text browser to display the user guide
        user_guide_text_browser = QTextBrowser(user_guide_dialog)
        html_file_path = "user_guide.html"  
        user_guide_text_browser.setSource(QUrl.fromLocalFile(html_file_path))
        user_guide_text_browser.setOpenExternalLinks(True)  # Allow opening external links

        # Create layout and add the text browser
        layout = QVBoxLayout()
        layout.addWidget(user_guide_text_browser)
        user_guide_dialog.setLayout(layout)

        user_guide_dialog.exec_()

    def parse_coordinate(self, text):
        """
        Parse a single input coordinate text and convert it to an integer.
        """
        try:
            return int(text.strip())
        except ValueError:
            QMessageBox.warning(self, "Format Error", "Please enter a valid integer coordinate.")
            return 0

    def close_application(self):
        """
        Exit the application.
        """
        record_log(self.log_file, self.user_name, "System Event", "System Shutdown")
        if self.plot_window is not None:
            self.plot_window.close()

        self.close()

    def load_images(self):
        """
        Load image folder,
        Initialize parameters,
        Start recursively displaying images.
        """

        self.images = []

        # If it's the first load, you can set a default path (commented out here)

        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder_path:
            return

        record_log(self.log_file, self.user_name, "System Event", "Loaded Image Folder: " + folder_path)
        self.current_folder = folder_path
        self.images = get_image_files(folder_path)
        self.is_first_load = False

        # Clear previous parameters if a standard image has not been selected
        self.area_data = {'bright_l': [], 'bright_m': [], 'bright_r': []}
        self.elongation_data = {'bright_l': [], 'bright_m': [], 'bright_r': []}
        self.std2min_data = []
        self.processed_images = []
        self.current_index = -1
        self.last_readable_img = ""

        self.infoTable.setRowCount(0)

        self.recursion_id = uuid.uuid4()  # Update recursion ID when starting a new load
        self.display_next_image(self.recursion_id)  # Pass the current ID

    def display_next_image(self, current_id):
        """
        Automatically and recursively update to the next image.
        """
        # Check if still in the current recursion sequence
        if current_id != self.recursion_id:
            return  # Stop recursion if not matching the current ID

        if self.is_on:
            if self.current_index < len(self.images) - 1:
                self.current_index += 1
                self.show_image(self.images[self.current_index])

        QTimer.singleShot(self.interval, lambda: self.display_next_image(current_id))

    def stop_analysis(self):
        self.is_on = False
        self.status_bar.showMessage("Analysis Stopped")
        record_log(self.log_file, self.user_name, "User Action", "User clicked Stop button")

    def continue_analysis(self):
        self.is_on = True
        record_log(self.log_file, self.user_name, "User Action", "User clicked Continue button")

    def check_for_new_images(self):
        """
        Check for new images and add them if found.
        """
        if not self.current_folder:
            return

        new_images = get_image_files(self.current_folder)
        if not new_images:
            return

        new_unique_images = [img for img in new_images if img not in self.images]

        for new_image in new_unique_images:
            self.images.append(new_image)

    def addRow(self, col1_data, col2_data, isException=True):
        row_position = self.infoTable.rowCount()
        self.infoTable.insertRow(row_position)

        # Set row height based on font size
        row_height = max(self.infoTable.fontMetrics().height() + 50, 20)
        self.infoTable.setRowHeight(row_position, row_height)

        # Create QTableWidgetItem instances and set data
        item1 = QTableWidgetItem(col1_data)
        item2 = QTableWidgetItem(col2_data)

        # Center-align the text
        item1.setTextAlignment(Qt.AlignCenter)
        item2.setTextAlignment(Qt.AlignCenter)

        # Set font color based on exception status
        if isException:
            redBrush = QBrush(QColor(128, 0, 0))
            item2.setForeground(redBrush)
        else:
            greenBrush = QBrush(QColor(0, 128, 0))
            item2.setForeground(greenBrush)

        # Add items to the table
        self.infoTable.setItem(row_position, 0, item1)
        self.infoTable.setItem(row_position, 1, item2)

        # Scroll to the bottom after adding a row
        self.infoTable.scrollToBottom()

    def show_image(self, image_path):
        # Display the processed image
        img = cut_image(image_path, self.image_coord, self.last_readable_img)
        self.last_readable_img = img
        img_with_labels, info, blocked = spot_detection(img, self.dark_rect)

        # If the image is blocked, use the most recent unblocked image temporarily
        if blocked:
            img = cut_image(self.not_blocked_img, self.image_coord, self.last_readable_img)
            img_with_labels, info, blocked = spot_detection(img, self.dark_rect)
            blocked = True

        std2min = compute_std_min_ratio(img, self.dark_rect)

        pixmap = convert_image_for_display(img_with_labels)

        image_name = split_timestamp_from_filename(os.path.basename(image_path))
        formatted_time = timestamp_to_datetime(image_name)

        # Save parameter data into a table
        record_data(self.data_file, image_name, formatted_time, std2min, info)

        # Update parameters
        update_info(info, self.area_data, self.elongation_data)
        self.std2min_data.append(std2min)

        # Update status bar
        if not blocked:
            self.not_blocked_img = image_path  # Save latest unblocked image
            self.status_bar.showMessage("Capture Time: " + formatted_time)
        else:
            self.status_bar.showMessage("Image Blocked by Window")

        # Update image UI component
        scaled_pixmap = pixmap.scaled(self.imageLabel.size(), aspectRatioMode=Qt.KeepAspectRatio)
        self.imageLabel.setPixmap(scaled_pixmap)
        self.imageLabel.adjustSize()
        self.imageLabel.setAlignment(Qt.AlignCenter)

        # Analyze parameters
        eval_result = spot_evaluation(image_path, info, self.area_data, self.elongation_data, self.std2min_data, blocked, self.thresholds)

        # Log parameter status
        if eval_result:
            self.addRow(formatted_time, eval_result, isException=True)
            record_log(self.log_file, self.user_name, "Image Status", eval_result, formatted_time)
            self.no_exception_count = 0
        else:
            self.no_exception_count += 1

        # If multiple consecutive images show no exceptions, show "No Exception"
        if self.no_exception_count >= self.thresholds['no_exception_count_threshold']:
            self.addRow(formatted_time, "No Exception", isException=False)
            record_log(self.log_file, self.user_name, "Image Status", "No Exception", formatted_time)
            self.no_exception_count = 0

        if image_path not in self.processed_images:
            self.processed_images.append(image_path)
            self.plot_window.update_plots(self.elongation_data, self.area_data, self.std2min_data)

    class CopyImagesThread(QThread):
        update_signal = pyqtSignal(str)  # Signal for updating status messages

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
                    # Skip copying if the file is in deleted records
                    if target_file in deleted_files or (self.only_new and os.path.exists(target_file)):
                        continue
                    try:
                        if not os.path.exists(target_file):
                            shutil.copy2(image_file, target_file)
                            self.update_signal.emit(f"File {os.path.basename(image_file)} copied to {self.target_folder}")
                        else:
                            continue
                        time.sleep(self.interval)
                    except Exception as e:
                        self.update_signal.emit(f"Error copying file {image_file}: {e}")

                # Check target folder and update deleted file records
                current_target_files = {os.path.join(self.target_folder, f) for f in os.listdir(self.target_folder) if os.path.isfile(os.path.join(self.target_folder, f))}
                source_files = {os.path.join(self.target_folder, os.path.basename(f)) for f in image_files}
                deleted_files.update(deleted_files.union(source_files) - current_target_files)