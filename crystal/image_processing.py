import cv2
import numpy as np
import os
import matplotlib.pyplot as plt
from PIL import Image
import time
from .utils import timestamp_to_datetime, split_timestamp_from_filename

def cut_image(image_path, image_area):
    img = cv2.imread(image_path)
    x1, y1, x2, y2 = image_area
    try:
        img = img[y1:y2, x1:x2]
        img = cv2.resize(img, (640, 480))
    except:
        img = np.zeros((480, 640, 3), dtype=np.uint8)
    return img

def preprocess_image(img):
    '''
    图像预处理
    '''
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (21, 21), 0)
    max_gray_level = np.max(blurred)
    threshold_value = 0.9 * max_gray_level
    _, thresh = cv2.threshold(blurred, threshold_value, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    closing = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    opening = cv2.morphologyEx(closing, cv2.MORPH_OPEN, kernel)
    bin_img = opening
    return bin_img

def detect_and_name_spots(bin_img, img):
    '''
    获取并返回光斑信息
    '''
    contours, _ = cv2.findContours(bin_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contour_img = img.copy()
    ellipses = []
    bright_spots_info = {}
    for i, cnt in enumerate(contours):
        if len(cnt) >= 5:
            hull = cv2.convexHull(cnt)
            ellipse = cv2.fitEllipse(hull)
            ellipses.append(ellipse)
            [(ex, ey), (l, s), angle] = ellipse
            elongation = max(l, s) / min(l, s)
            bright_spots_info[i] = {
                "centroid": (ex, ey),
                "area": cv2.contourArea(hull),
                "elongation": elongation,
                "convex":hull
            }

    num_spots = len(bright_spots_info)
    sorted_indices = sorted(bright_spots_info.keys(), key=lambda k: bright_spots_info[k]['centroid'][0])

    if num_spots == 3:
        named_indices = {idx: name for idx, name in zip(sorted_indices, ['bright_l', 'bright_m', 'bright_r'])}
    else:
        named_indices = {idx: name for idx, name in zip(sorted_indices, ['bright_m', 'bright_l', 'bright_r'])}

    info = {new: bright_spots_info[old] for old, new in named_indices.items()}
    return contour_img, info, ellipses


def draw_and_label(contour_img, info, ellipses, rect):
    '''
    在图像上绘制光斑相关属性
    '''
    for name, spot in info.items():
        ex, ey = spot['centroid']
        hull = spot['convex']
        for ellipse in ellipses:
            [(ellipse_x, ellipse_y), _, _] = ellipse
            if int(ellipse_x) == int(ex) and int(ellipse_y) == int(ey):
                cv2.drawContours(contour_img, [hull], 0, (0, 0, 255), 2)
                cv2.ellipse(contour_img, ellipse, (0, 255, 0), 2)
                cv2.circle(contour_img, (int(ex), int(ey)), 5, (255, 0, 0), -1)
                cv2.putText(contour_img, name, (int(ex), int(ey - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                break

    x1, y1, x2, y2 = rect
    cv2.rectangle(contour_img, (x1, y1), (x2, y2), (0, 255, 0), 2)

    return contour_img


def spot_detection(image_path, rect, image_area):
    '''
    光斑检测函数，返回绘制后图像、光斑信息、图像路径
    '''
    img = cut_image(image_path, image_area)
    bin_img = preprocess_image(img)
    contour_img, info, ellipses = detect_and_name_spots(bin_img, img)
    contour_img = draw_and_label(contour_img, info, ellipses, rect)
    contour_img = cv2.cvtColor(contour_img, cv2.COLOR_BGR2RGB)
    contour_img = Image.fromarray(contour_img)
    return contour_img, info, os.path.basename(image_path)

def compute_std_min_ratio(image_path, rect, image_area):
    """
    Computes the ratio of the standard deviation to the minimum grayscale value in a specified 
    rectangular region of an image.

    :param image_path: Path to the image file.
    :param rect: A tuple (x1, y1, x2, y2) 
    :return: Ratio of the standard deviation to the minimum grayscale value in the region.
    """
    image = cut_image(image_path, image_area)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)   
    x1, y1, x2, y2 = rect
    sub_image = image[y1:y2, x1:x2]
    hist = cv2.calcHist([sub_image], [0], None, [256], [0, 256]).flatten()
    std_dev = np.std(hist)
    min_val = (np.min(sub_image) / 255) * 100
    if min_val == 0:
        return float('inf')

    return std_dev / min_val


def compute_brightness(image_path, image_area):

    image = cut_image(image_path, image_area)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mask = (image > 10)

    filtered_image = image[mask]

    height, width = image.shape
    upper_part_mask = mask[:height // 2, :]
    middle_part_mask = mask[height // 4: 3 * height // 4, :]

    upper_part = image[:height // 2, :][upper_part_mask[:height // 2, :]]
    middle_part = image[height // 4: 3 * height // 4, :][middle_part_mask]

    upper_brightness = np.mean(upper_part) if upper_part.size > 0 else 0
    middle_brightness = np.mean(middle_part) if middle_part.size > 0 else 0
    overall_brightness = np.mean(filtered_image) if filtered_image.size > 0 else 0

    upper_weight = 0.4  
    middle_weight = 0.4 
    overall_weight = 0.2

    weighted_avg_brightness = (upper_brightness * upper_weight +
                               middle_brightness * middle_weight +
                               overall_brightness * overall_weight)

    return weighted_avg_brightness

def spot_evaluation(image_path, info, area_data, elongation_data, std2min_data):

    image_filename = os.path.basename(image_path)
    image_name = split_timestamp_from_filename(image_filename)

    formatted_time = timestamp_to_datetime(image_name)

    if len(info) < 3:
        return image_filename + " " + formatted_time + "\n不正常"

    if std2min_data[-1] - std2min_data[0] < -0.6:
        return image_filename + " " + formatted_time + "\n暗斑 异常"

    if area_data['bright_l'][-1]  - area_data['bright_l'][0] < -800:
        return image_filename + " " + formatted_time + "\n面积 异常"

    if area_data['bright_l'][-1]  - area_data['bright_l'][0] > 800:
        return image_filename + " " + formatted_time + "\n面积 异常"

    if elongation_data['bright_r'][-1]  - elongation_data['bright_r'][0] > 0.1:
        return image_filename + " " + formatted_time + "\n亮斑 变细"



    # area = area_data[-1] - area_data[0]


if __name__ == "__main__":
    img_path = './data/455-1.png'
    img = cv2.imread(img_path)

    processed_img, info, path = spot_detection(img_path)

    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    plt.title('Original Image')
    plt.axis('off')

    plt.subplot(1, 2, 2)
    plt.imshow(processed_img)
    plt.title('Processed Image')
    plt.axis('off')

    plt.show()
