import os
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QLabel, QTextEdit, QWidget, QFileDialog, QPushButton
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt,QTimer
from .image_processing import spot_detection, compute_std_min_ratio, spot_evaluation, compute_brightness
from .utils import get_image_files, convert_image_for_display, update_info
import time

class ImageWindow(QMainWindow):
    def __init__(self, area_window, elongation_window, std2min_window, brightness_window, interval, image_area):
        super().__init__()

        self.area_window = area_window
        self.elongation_window = elongation_window
        self.std2min_window = std2min_window
        self.brightness_window = brightness_window
        # self.hist_window = hist_window

        self.setWindowTitle("晶体图像分析")
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        self.imageLabel = QLabel(self)
        layout.addWidget(self.imageLabel)

        self.infoBox = QTextEdit(self)
        font = QFont()
        font.setPointSize(30)  
        self.infoBox.setFont(font)  
        layout.addWidget(self.infoBox)

        self.openDirectoryButton = QPushButton("打开文件夹", self)
        self.openDirectoryButton.clicked.connect(self.load_images)
        layout.addWidget(self.openDirectoryButton)

        self.exitButton = QPushButton("退出", self)
        self.exitButton.clicked.connect(self.close_application)
        layout.addWidget(self.exitButton)

        centralWidget = QWidget()
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)

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
        self.timer.start(100)  

        self.interval = interval
        self.image_area = image_area

    def close_application(self):
        '''
        退出软件
        '''
        if self.area_window is not None:
            self.area_window.close()
        if self.elongation_window is not None:
            self.elongation_window.close()
        if self.std2min_window is not None:
            self.std2min_window.close()
        # if self.hist_window is not None:
        #     self.hist_window.close()
        if self.brightness_window is not None:
            self.brightness_window.close()

        self.close()

    def load_images(self):
        folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        # folder_path = './data/test'
        if not folder_path:
            return

        self.current_folder = folder_path
        self.images = get_image_files(folder_path)
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

        if len(new_images) > len(self.images):
            for new_image in new_images[len(self.images):]:
                self.images.append(new_image)
                self.show_image(new_image)

    def show_image(self, image_path):
        # self.infoBox.clear()

        rect = (204,60,204+330,60+74)

        image, info, image_name = spot_detection(image_path, rect, self.image_area)
        std2min = compute_std_min_ratio(image_path, rect, self.image_area)
        brightness = compute_brightness(image_path, self.image_area)
        pixmap = convert_image_for_display(image)

        # 将时间戳转换为本地时间
        local_time = time.localtime(int(os.path.splitext(image_name)[0]))

        # 格式化为年月日时分秒
        formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
        self.setWindowTitle(formatted_time)
        self.imageLabel.setPixmap(pixmap)
        self.imageLabel.adjustSize()

        update_info(info, self.area_data, self.elongation_data)
        self.std2min_data.append(std2min)
        self.brightness_data.append(brightness)

        eval_result = spot_evaluation(image_path, info, self.area_data, self.elongation_data, self.std2min_data)
        self.infoBox.append(eval_result)

        if image_path not in self.processed_images: 
            self.processed_images.add(image_path)  
            self.area_window.update_plot(self.area_data)  
            self.elongation_window.update_plot(self.elongation_data)
            self.std2min_window.update_plot(self.std2min_data)
            self.brightness_window.update_plot(self.brightness_data)
            # self.hist_window.update_plot([param - self.elongation_data['bright_l'][0] for param in self.elongation_data['bright_l']])
            # self.hist_window.update_plot([param - self.std2min_data[0] for param in self.std2min_data])


