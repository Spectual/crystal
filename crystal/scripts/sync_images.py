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
    # parser.add_argument('-i', '--input', help='source folder', dest='source_folder', default=r"\\192.168.4.170\test")
    parser.add_argument('-i', '--input', help='source folder', dest='source_folder', default=r"data\test")
    parser.add_argument('-o', '--output', help='target folder ', dest='target_folder', default=r'data\test')
if system == "Darwin":
    parser.add_argument('-i', '--input', help='source folder', dest='source_folder', default="./data/73")
    parser.add_argument('-o', '--output', help='target folder ', dest='target_folder', default="./data/test")

args = parser.parse_known_args()[0]

deleted_files = set()  # 维护一个已删除文件的集合


def copy_images_periodically(source_folder, target_folder, interval):
    global deleted_files
    while True:
        image_files = get_image_files(source_folder)
        for image_file in image_files:
            target_file = os.path.join(target_folder, os.path.basename(image_file))
            # 如果文件在已删除记录中，则跳过复制
            if target_file in deleted_files:
                continue
            try:
                if not os.path.exists(target_file):
                    shutil.copy2(image_file, target_file)
                    print(f"文件 {os.path.basename(image_file)} 已被复制到 {target_folder}")
                else:
                    # 如果文件已存在且不在已删除记录中，仍然跳过复制
                    continue
                time.sleep(interval)
            except Exception as e:  # 使用具体的异常类型替代通用的异常捕获
                print(f"复制文件 {image_file} 时发生错误: {e}")

        # 检查目标文件夹，更新已删除文件记录
        current_target_files = {os.path.join(target_folder, f) for f in os.listdir(target_folder) if
                                os.path.isfile(os.path.join(target_folder, f))}
        source_files = {os.path.join(target_folder, os.path.basename(f)) for f in image_files}
        deleted_files.update(deleted_files.union(source_files) - current_target_files)


def run():
    copy_images_periodically(args.source_folder, args.target_folder, args.interval)


if __name__ == "__main__":
    run()
