﻿# !/usr/bin/env python
# _*_ coding:utf-8 _*_

__author__ = 'bai xu'
__date__ = '18/01/22'

import subprocess
import requests
import random
import os
import sys
# import re

from PIL import Image
from aip import AipOcr
from io import BytesIO
# from bs4 import BeautifulSoup
# from pyocr import pyocr

# 全局变量只是为了使用tesseract OCR时收集数据集用
i = random.randint(1, 100)
DEBUG_SWITCH = False
VERSION = '1.0.1'

config = {
    '头脑王者': {
        'title': (80, 500, 1000, 880),
        'answers': (80, 960, 1000, 1720),
        'point': [
            (316, 993, 723, 1078),
            (316, 1174, 723, 1292),
            (316, 1366, 723, 1469),
            (316, 1570, 723, 1657)


        ]
    },
    '西瓜视频': {
        'box': (80, 400, 1000, 1250)
    }
}


def get_screenshot():
    """获取手机截图"""

    process = subprocess.Popen("adb shell screencap -p", shell=True, stdout=subprocess.PIPE)
    screenshot = process.stdout.read()

    # print(screenshot)
    # b"\x89PNG\r\r\r\n\x1a\r\r\n\x00\x00\x00\rIHDR\x00\x00\x048\x00\x00\x07\x80\x08\x06\x00\
    # 上面是一个PNG格式的图片，但需要将格式化（换行替换)
    screenshot = screenshot.replace(b'\r\r\n', b'\n')
    ######################################################
    # 测试用，实际直接环境直接在内存内操作，减少读写IO
    if DEBUG_SWITCH:
        global i
        i = i + 1
        with open('question'+str(i) + '.png', 'wb') as f:
            f.write(screenshot)
    ######################################################
    # img_fb副本文件句柄
    img_fb = BytesIO()
    img_fb.write(screenshot)
    img = Image.open(img_fb)
    # 对图片关键信息裁剪
    title_img = img.crop((80, 500, 1000, 880))
    answers_img = img.crop((80, 960, 1000, 1720))
    # 拼接图片画布
    new_img = Image.new('RGBA', (920, 1140))
    new_img.paste(title_img, (0, 0, 920, 380))
    new_img.paste(answers_img, (0, 380, 920, 1140))
    # 内存对象
    new_img_fb = BytesIO()
    new_img.save(new_img_fb, 'png')
    ######################################################
    # 测试用
    if DEBUG_SWITCH:
        with open('test.png', 'wb') as f:
            f.write(new_img_fb.getvalue())
    ######################################################
    return new_img_fb


def get_word_by_image(img):
    """从百度OCR获取文字"""
    app_id = '10731656'
    api_key = 'ZeGHQUlwVvMY9fFl81P12WD9'
    secret_key = 'Oy3FdgBajMlBf1utUcUMT7I6PyfKLRji'
    client = AipOcr(app_id, api_key, secret_key)
    res = client.basicGeneral(img)
    return res


def baidu(question, answers):
    """搜索并且算出最有可能的答案"""
    url = 'https://www.baidu.com/s'
    headers = {
        'User-Agent': 'Mozilla/5.0 \
        (Windows NT 10.0; Win64; x64) \
        AppleWebKit/537.36 (KHTML, like Gecko) \
        Chrome/63.0.3239.132 Safari/537.36'
    }
    data = {
        'wd': question
    }
    res = requests.get(url, params=data, headers=headers)
    res.encoding = 'utf-8'
    html = res.text
    # 分析最有可能答案
    for t in range(len(answers)):
        # 出现次数、answers、序号
        answers[t] = (html.count(answers[t]), answers[t], t)
    answers.sort(reverse=True)
    return answers


def click(point):
    cmd = 'adb shell input swipe %s %s %s %s %s' % (point[0],
                                                    point[1],
                                                    point[0] + random.randint(0, 3),
                                                    point[1] + random.randint(0, 3),
                                                    200)
    os.system(cmd)


def run():

    print("头脑王者答题助手" + VERSION)
    device_str = os.popen('adb shell getprop ro.product.device').read()
    if not device_str:
        print('请安装 ADB 及驱动并配置环境变量')
        sys.exit(0)
    print(device_str.replace("\n", "") + "设备已就绪")
    while True:
        instruction = input("在题目完整显示后回车，退出输入q")
        if instruction == "\0":
            continue
        elif instruction == "v":
            print(VERSION)
            break
        elif instruction == "g":
            print("https://github.com/by777/smartest_brain")
            break
        elif instruction == "q":
            sys.exit(0)
        device_str_ = os.popen('adb shell getprop ro.product.device').read()
        if not device_str_:
            print('请检查手机是否已连接电脑')
            sys.exit(0)
        img = get_screenshot()
        info = get_word_by_image(img.getvalue())
        if info['words_result_num'] < 5:
            print("本次关键信息识别失败")
            continue
        question = ''.join([x['words'] for x in info['words_result'][:-4]])
        answers = [x['words'] for x in info['words_result'][-4:]]
        print("Q: " + question)
        res = baidu(question, answers)
        print("A: " + res[0][1])
        click(config['头脑王者']['point'][res[0][2]])
        print("------------------------")


if __name__ == '__main__':
    run()