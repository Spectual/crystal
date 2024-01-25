import os
from PyQt5.QtGui import QImage, QPixmap
import numpy as np
import time

def split_timestamp_from_filename(image_filename):
    '''
    input: "123.png"
    output: 123
    '''
    try:
        return int(os.path.splitext(image_filename)[0])
        
    except ValueError:
        return os.path.splitext(image_filename)[0]

def timestamp_to_datetime(timestamp):
    # 将时间戳转换为年月日时分秒
    if not isinstance(timestamp, int):
        return timestamp
    date_time = time.localtime(timestamp)
    formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", date_time)
    return formatted_time

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

def update_first_info(info, area_data, elongation_data):
    # 填入为第一个元素
    detected_spots = set(info.keys())

    for name in ['bright_l', 'bright_m', 'bright_r']:
        if name in detected_spots:
            area_data[name].insert(0, info[name]['area'])
            elongation_data[name].insert(0, info[name]['elongation'])
        else:
            elongation_data[name].insert(0, np.nan)
            area_data[name].insert(0, np.nan)

def get_image_files(folder_path):
    if not folder_path:
        return []

    image_files = sorted(
        [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))],
        key=lambda x: int(x.split('-')[0].split('.')[0])
    )

    images = [os.path.join(folder_path, image_file) for image_file in image_files]

    return images



if __name__ == "__main__":
    print(get_image_files('./data'))