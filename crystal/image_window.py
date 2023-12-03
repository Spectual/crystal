import os
import cv2
import numpy as np
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QPushButton, QLabel, QTextEdit, QWidget, QFileDialog
from PyQt5.QtGui import QPixmap, QImage
from PIL import Image
from .image_processing import spot_detection
from .utils import get_image_files,convert_image_for_display, update_info_box

class ImageWindow(QMainWindow):
    def __init__(self, area_window, elongation_window):
        super().__init__()

        self.area_window = area_window
        self.elongation_window = elongation_window

        self.setWindowTitle("光斑提取")
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        self.imageLabel = QLabel(self)
        layout.addWidget(self.imageLabel)

        self.infoBox = QTextEdit(self)
        layout.addWidget(self.infoBox)

        self.openDirectoryButton = QPushButton("打开文件夹", self)
        self.openDirectoryButton.clicked.connect(self.load_images)
        layout.addWidget(self.openDirectoryButton)

        self.prevButton = QPushButton("上一张", self)
        self.prevButton.clicked.connect(self.show_prev_image)
        layout.addWidget(self.prevButton)

        self.nextButton = QPushButton("下一张", self)
        self.nextButton.clicked.connect(self.show_next_image)
        layout.addWidget(self.nextButton)

        centralWidget = QWidget()
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)

        self.images = []
        self.current_index = 0
        self.area_data = {'bright_l': [], 'bright_m': [], 'bright_r': []}

        self.elongation_data = {'bright_l': [], 'bright_m': [], 'bright_r': []}

        self.processed_images = set()

        self.elongation_window = elongation_window

    def load_images(self):
        '''
        选择并加载文件夹中图像
        '''
        folder_path = QFileDialog.getExistingDirectory(self, "Select Image Directory")
        # folder_path = "./data/27"
        if not folder_path:
            return
            
        self.images = get_image_files(folder_path)

        if self.images:
            self.current_index = 0
            self.show_image(self.images[self.current_index])

    def show_image(self, image_path):
        '''
        调用spot_detection处理图像，获取光斑的信息并展示处理后的图像
        更新Area和Elongation图表
        '''
        self.infoBox.clear()

        image, info, image_name = spot_detection(image_path)
        pixmap = convert_image_for_display(image)

        self.setWindowTitle(image_name)
        self.imageLabel.setPixmap(pixmap)
        self.imageLabel.adjustSize()

        update_info_box(self.infoBox, info, self.area_data, self.elongation_data)

        if image_path not in self.processed_images: 
            self.processed_images.add(image_path)  
            self.area_window.update_plot(self.area_data)  
            self.elongation_window.update_plot(self.elongation_data)

    def show_prev_image(self):
        if self.images and self.current_index > 0:
            self.current_index -= 1
            self.show_image(self.images[self.current_index])

    def show_next_image(self):
        if self.images and self.current_index < len(self.images) - 1:
            self.current_index += 1
            self.show_image(self.images[self.current_index])
