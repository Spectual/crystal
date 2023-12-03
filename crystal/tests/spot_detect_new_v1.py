'''
面积相比第一个变化

'''
import sys
import os
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QVBoxLayout, QPushButton, QLabel, QTextEdit, QWidget
from PyQt5.QtGui import QPixmap, QImage
from skimage import morphology, measure
from skimage.segmentation import watershed
from skimage.feature import peak_local_max
from scipy import ndimage
from scipy.ndimage import binary_fill_holes
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PIL import Image, ImageDraw, ImageQt


class ImageWindow(QMainWindow):
    def __init__(self, plot_window, elongation_window):
        super().__init__()

        self.plot_window = plot_window
        self.elongation_window = elongation_window

        self.setWindowTitle("光斑提取")
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        self.imageLabel = QLabel(self)
        layout.addWidget(self.imageLabel)

        self.infoBox = QTextEdit(self)
        layout.addWidget(self.infoBox)

        self.openDirectoryButton = QPushButton("Open Directory", self)
        self.openDirectoryButton.clicked.connect(self.load_images)
        layout.addWidget(self.openDirectoryButton)

        self.prevButton = QPushButton("Previous", self)
        self.prevButton.clicked.connect(self.show_prev_image)
        layout.addWidget(self.prevButton)

        self.nextButton = QPushButton("Next", self)
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
        folder_path = QFileDialog.getExistingDirectory(self, "Select Image Directory")
        # folder_path = "/Users/spectual/Documents/Total/Project/crystal/RHEED/RHEED-Data/46号带-差/png"
        if not folder_path:
            return

        self.area_data = {'bright_l': [], 'bright_m': [], 'bright_r': []}
        image_files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))],
                             key=lambda x: int(x.split('-')[0]))
        self.images = [os.path.join(folder_path, image_file) for image_file in image_files]

        if self.images:
            self.current_index = 0
            self.show_image(self.images[self.current_index])

    def show_image(self, image_path):
        self.infoBox.clear()

        image, info, image_name = self.process_image(image_path)

        qim = QImage(image.tobytes('raw', 'RGB'), image.width, image.height, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qim)


        self.setWindowTitle(image_name)

        self.imageLabel.setPixmap(pixmap)
        self.imageLabel.adjustSize()

        detected_spots = set(info.keys())

        for name in ['bright_l', 'bright_m', 'bright_r']:
            if name in detected_spots:
                self.infoBox.append(f"{name}:")
                self.infoBox.append(f"  centroid = {info[name]['centroid']}")
                self.infoBox.append(f"  area = {info[name]['area']}\n")
                self.area_data[name].append(info[name]['area'])
                self.elongation_data[name].append(info[name]['elongation'])
                print(self.area_data)  
            else:
                self.elongation_data[name].append(np.nan)  
                self.area_data[name].append(np.nan)

        if image_path not in self.processed_images: 
            self.processed_images.add(image_path)  
            self.plot_window.update_plot(self.area_data)  
            self.elongation_window.update_plot(self.elongation_data)  

    def show_prev_image(self):
        if self.images and self.current_index > 0:
            self.current_index -= 1
            self.show_image(self.images[self.current_index])

    def show_next_image(self):
        if self.images and self.current_index < len(self.images) - 1:
            self.current_index += 1
            self.show_image(self.images[self.current_index])


    def process_image(self, image_path):

        img = cv2.imread(image_path)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        blurred = cv2.GaussianBlur(gray, (21, 21), 0)
        

        max_gray_level = np.max(blurred)

        threshold_value = 0.9 * max_gray_level
        

        _, thresh = cv2.threshold(blurred, threshold_value, 255, cv2.THRESH_BINARY)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        closing = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        opening = cv2.morphologyEx(closing, cv2.MORPH_OPEN, kernel)
        

        contours, _ = cv2.findContours(opening, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        

        contour_img = img.copy()
        ellipses = []
        bright_spots_info = {}
        for i,cnt in enumerate(contours):
            if len(cnt) >= 5:  
                hull = cv2.convexHull(cnt)
                cv2.drawContours(contour_img, [hull], 0, (0, 0, 255), 2)

                ellipse = cv2.fitEllipse(hull)
                ellipses.append(ellipse)

                [(ex, ey), (l, s), angle] = ellipse
                elongation = max(l,s) / min(l,s)
                bright_spots_info[i] = {
                    "centroid": (ex, ey),
                    "area": cv2.contourArea(hull),
                    "elongation": elongation  
                }           

            cv2.circle(contour_img, (int(ex), int(ey)), 5, (255, 0, 0), -1)  
            cv2.ellipse(contour_img, ellipse, (0, 255, 0), 2)

        num_spots = len(ellipses)

        sorted_indices = sorted(bright_spots_info.keys(), key=lambda k: bright_spots_info[k]['centroid'][0])
        # print(bright_spots_info.keys())
        if num_spots == 3:
            named_indices = {idx: name for idx, name in zip(sorted_indices, ['bright_l', 'bright_m', 'bright_r'])}
        else:
            named_indices = {idx: name for idx, name in zip(sorted_indices, ['bright_m', 'bright_l', 'bright_r'])}

        info = {}
        for old, new in named_indices.items():
            info[new] = bright_spots_info[old]
        
        detected_spots = set(info.keys())
        for name in ['bright_l', 'bright_m', 'bright_r']:
            if name in detected_spots:
                cx, cy = info[name]['centroid']
                cv2.putText(contour_img, name, (int(cx), int(cy-10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)


        contour_img = cv2.cvtColor(contour_img, cv2.COLOR_BGR2RGB)
        contour_img = Image.fromarray(contour_img)
        return contour_img, info, os.path.basename(image_path)

class ElongationPlotWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Elongation Changes")
        self.setGeometry(1300, 100, 600, 400)

        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvas(self.fig)
        self.setCentralWidget(self.canvas)

    def update_plot(self, elongation_data):
        self.ax.clear()

        x = list(range(len(elongation_data['bright_l'])))
        for name, elongations in elongation_data.items():
            self.ax.plot(x, elongations, label=name)

        self.ax.legend()
        self.ax.set_xlabel('Image Index')
        self.ax.set_ylabel('Elongation')
        self.canvas.draw()


class PlotWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Area Changes")
        self.setGeometry(700, 100, 600, 400)

        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvas(self.fig)
        self.setCentralWidget(self.canvas)

    def update_plot(self, area_data):
        self.ax.clear()

        x = list(range(len(area_data['bright_l'])))
        for name, areas in area_data.items():
            self.ax.plot(x, [area - areas[0] for area in areas], label=name, marker='o')

        self.ax.legend()
        self.ax.set_xlabel('Image Index')
        self.ax.set_ylabel('Area')
        self.canvas.draw()


app = QApplication(sys.argv)
plot_window = PlotWindow()
plot_window.show()
elongation_plot_window = ElongationPlotWindow()
image_window = ImageWindow(plot_window, elongation_plot_window)
elongation_plot_window.show()
image_window.show()
app.exec_()
