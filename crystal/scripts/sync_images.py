
import os
import platform
import shutil
import time
from ..utils import get_image_files

import argparse

system = platform.system()

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--interval', help='time interval (second)', dest='interval', type=float, default=1)
if system == "Windows":
    parser.add_argument('-i', '--input', help='source folder', dest='source_folder', default=r"\\192.168.4.170\test")
    parser.add_argument('-o', '--output', help='target folder ', dest='target_folder', default=r'data\test')
if system == "Darwin":
    parser.add_argument('-i', '--input', help='source folder', dest='source_folder', default="/Volumes/Avocado/crystal/73")
    parser.add_argument('-o', '--output', help='target folder ', dest='target_folder', default="/Volumes/Avocado/crystal/test")

args = parser.parse_known_args()[0]

def copy_images_periodically(source_folder, target_folder, interval):
    """
    :param source_folder: 源文件夹路径
    :param target_folder: 目标文件夹路径
    :param interval: 复制图片的时间间隔（秒）
    """
    while True:
        image_files = get_image_files(source_folder)
        for image_file in image_files:
            target_file = os.path.join(target_folder, os.path.basename(image_file))
            try:
                if not os.path.exists(target_file):
                    shutil.copy2(image_file, target_file)
                    print(f"文件 {os.path.basename(image_file)} 已被复制到 {target_folder}")
            except:
                print(image_file,"不存在")

            time.sleep(interval)                 

def run():
    copy_images_periodically(args.source_folder, args.target_folder, args.interval)

if __name__ == "__main__":
    run()
