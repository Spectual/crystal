
import os
import shutil
import time
from ..utils import get_image_files

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--interval', help='time interval (second)', dest='interval', type=float, default=1)
parser.add_argument('-i', '--input', help='source folder', dest='source_folder', default='data/46')
parser.add_argument('-o', '--output', help='target folder ', dest='target_folder', default='data/test')

args = parser.parse_known_args()[0]

def copy_images_periodically(source_folder, target_folder, interval):
    """
    :param source_folder: 源文件夹路径
    :param target_folder: 目标文件夹路径
    :param interval: 复制图片的时间间隔（秒）
    """
    image_files = get_image_files(source_folder)
    for image_file in image_files:
        target_file = os.path.join(target_folder, os.path.basename(image_file))
        shutil.copy2(image_file, target_file)
        print(f"文件 {os.path.basename(image_file)} 已被复制到 {target_folder}")
        time.sleep(interval)

def run():
    copy_images_periodically(args.source_folder, args.target_folder, args.interval)

if __name__ == "__main__":
    run()
