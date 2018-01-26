# !/usr/bin/env python
# _*_ coding:utf-8 _*_

__author__ = 'bai xu'
__date__ = '18/01/22'

##############################################
# 此beta版本作训练用
# OCR识别部分使用Tesseract OCR
# 计算答案部分使用文本相似度分析
##############################################

import subprocess
import requests
import random
import os
import sys
import numpy as np
import re

from pyocr import pyocr
from PIL import Image
from io import BytesIO
from bs4 import BeautifulSoup

# 如果遇到Tesseract OCR报错，请尝试取消注释，并修改相应的路径
# os.chdir('C:\ProgramData\Anaconda3\Lib\site-packages\pyocr')
# os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'
DEBUG_SWITCH = False

i = random.randint(1, 1000)
VERSION = 'Beta-1.0.1'
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
    process = subprocess.Popen("adb shell screencap -p", shell=True, stdout=subprocess.PIPE)
    screenshot = process.stdout.read()
    screenshot = screenshot.replace(b'\r\r\n', b'\n')
    if DEBUG_SWITCH:
        with open('question'+str(i)+'.png', 'wb') as f:
            f.write(screenshot)
    img_fb = BytesIO()
    img_fb.write(screenshot)
    img = Image.open(img_fb)
    title_img = img.crop((80, 500, 1000, 880))
    answers_img = img.crop((80, 960, 1000, 1720))
    new_img = Image.new('RGBA', (920, 1140))
    new_img.paste(title_img, (0, 0, 920, 380))
    new_img.paste(answers_img, (0, 380, 920, 1140))
    new_img_fb = BytesIO()
    new_img.save(new_img_fb, 'png')
    return new_img_fb


def get_pic_crop(img):
    img_fb = BytesIO()
    img_fb.write(img.getvalue())
    img = Image.open(img_fb)
    title_img = img.crop((80, 500, 1000, 880))
    answers_img_1 = img.crop((240, 970, 840, 1110))
    # answers_img_1 = answers_img_1.convert('1')
    answers_img_2 = img.crop((240, 1160, 840, 1310))
    answers_img_3 = img.crop((240, 1350, 840, 1500))
    answers_img_4 = img.crop((240, 1540, 840, 1690))
    answers_imgs = {'title_img': title_img,
                    'answers_img_1': answers_img_1,
                    'answers_img_2': answers_img_2,
                    'answers_img_3': answers_img_3,
                    'answers_img_4': answers_img_4}
    return answers_imgs


def get_word_by_image(img):
    """从本地OCR获取文字（DEBUG_SWITCH = True时收集训练样本）"""
    tools = pyocr.get_available_tools()[:]
    if len(tools) == 0:
        print("No OCR tool found")
        sys.exit(1)
    # print("Using '%s'" % (tools[0].get_name()))
    print(tools[0].image_to_string(img, lang='chi_sim'))
    return tools[0].image_to_string(img, lang='chi_sim')


def baidu(keyword):
    """搜索内容相关度"""
    url = 'https://www.baidu.com/s'
    headers = {
        'User-Agent': 'Mozilla/5.0 \
        (Windows NT 10.0; Win64; x64) \
        AppleWebKit/537.36 (KHTML, like Gecko) \
        Chrome/63.0.3239.132 Safari/537.36'
    }
    data = {
        'wd': keyword
    }
    res = requests.get(url, params=data, headers=headers)
    if res.status_code != '200':
        print("检查网络状况")
        sys.exit(0)
    res.encoding = 'utf-8'
    bs = BeautifulSoup(res.text, 'lxml')
    exp1 = bs.find('div', attrs={'class': 'nums'})
    text = exp1.get_text()
    num = re.sub(r'\D', "", text)
    print(keyword+"相关结果约", num)
    return int(num)


def click(point):
    cmd = 'adb shell input swipe %s %s %s %s %s' % (point[0],
                                                    point[1],
                                                    point[0] + random.randint(0, 3),
                                                    point[1] + random.randint(0, 3),
                                                    200)
    os.system(cmd)


def get_answer(question, answers):
    question_num = baidu(question)
    answer_num = []
    question_answers_num = []
    for answer in answers:
        answer_num.append(baidu(answer))
        question_answers_num.append(baidu((question + " " + answer)))
    answer_num = np.array(answer_num, dtype='int64')
    question_answers_num = np.array(question_answers_num, dtype='int64')
    question_num = np.array(question_num, dtype='int64')
    correlation = question_answers_num / (question_num * answer_num)
    correlation = correlation.tolist()
    print("题目是{0}")
    correlation_index = correlation.index((max(correlation)))
    return correlation_index


def run():
    answers = []
    question = ""
    print("头脑王者答题助手" + VERSION)
    device_str = os.popen('adb shell getprop ro.product.device').read()
    if not device_str:
        print('请检查ADB文件及手机USB调试模式')
        sys.exit(0)
    print(device_str.replace("\n", "") + "设备已就绪")
    while True:
        instruction = input("在题目完整显示后回车，退出输入q\n")
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
            print('手机连接已中断，即将退出')
            sys.exit(0)
        img = get_screenshot()
        question_answers_imgs = get_pic_crop(img)
        for key in question_answers_imgs:
            if key == 'title_img':
                question = get_word_by_image(question_answers_imgs[key])
            else:
                answer = get_word_by_image(question_answers_imgs[key])
                answers.append(answer)
        if len(answers) < 4:
            print("本次识别失败，请继续训练Tesseracr OCR")
            continue
        where = get_answer(question, answers)
        click(config['头脑王者']['point'][where])


if __name__ == '__main__':
    run()
