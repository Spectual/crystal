import os
from PyQt5.QtGui import QImage, QPixmap
import numpy as np

def convert_image_for_display(image):
    qim = QImage(image.tobytes('raw', 'RGB'), image.width, image.height, QImage.Format_RGB888)
    return QPixmap.fromImage(qim)

def update_info(info, area_data, elongation_data):
    detected_spots = set(info.keys())

    for name in ['bright_l', 'bright_m', 'bright_r']:
        if name in detected_spots:
            area_data[name].append(info[name]['area'])
            elongation_data[name].append(info[name]['elongation'])
        else:
            elongation_data[name].append(np.nan)  
            area_data[name].append(np.nan)

def get_image_files(folder_path):
    if not folder_path:
        return []

    # image_files = sorted(
    #     [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))],
    #     key=lambda x: int(x.split('-')[0])
    # )
    image_files = sorted(
        [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))],
        key=lambda x: int(os.path.splitext(x)[0])  # 直接将文件名转换为整数进行排序
    )
    images = [os.path.join(folder_path, image_file) for image_file in image_files]

    return images



if __name__ == "__main__":
    print(get_image_files('./data'))