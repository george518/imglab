import numpy
import urllib.request
from PIL import Image, ImageDraw
import random
import io
import math
import os

# 初始化应用文件夹

if not os.path.exists('cache'):
    os.mkdir('cache') # 用于缓存远程图片

if not os.path.exists('save'):
    os.mkdir('save') # 用于保存输出图片

# 初始化设备常量

def createScreenWidth(device): # 工厂模式
    r = 750 # 默认值
    if device == 'iphone':
        r = 750
    return r

screen_width = createScreenWidth('iphone') # iPhone 默认屏幕宽度


# 图像处理模块

def getImageFromURL(img_url): # 通过 URL 获取图像数据
    img_file = urllib.request.urlopen(img_url)
    img_bytes = io.BytesIO(img_file.read())
    r = Image.open(img_bytes)
    return r

def compareColor(rgb_1,rgb_2): # 颜色 RGB 方差比较计算
    r = (rgb_1[0] - rgb_2[0]) ** 2 + (rgb_1[1] - rgb_2[1]) ** 2 + (rgb_2[2] - rgb_2[2]) ** 2
    return r

def getCoreBox(img_input): # 切除多余背景（白边 or 纯色边）
    img_array = img_input.load()
    bg_color = img_array[0,0] # 取第一个像素的颜色值作为背景参考色
    img_width = img_input.size[0]
    img_height = img_input.size[1]
    x1 = 0 # 确定左边界
    sum = 0
    for i in range(0,img_width):
        x1 = i
        for j in range(0,img_height):
            sum = sum + compareColor(img_array[i,j],bg_color)
        if (sum / img_height) > 2:
            break
    x2 = 0 # 确定右边界
    sum = 0
    for i in range(0,img_width):
        # x2 = img_width - i - 1
        x2 = img_width - i - 1
        for j in range(0,img_height):
            sum = sum + compareColor(img_array[x2,j],bg_color)
        if (sum / img_height) > 2:
            break
    y1 = 0 # 确定上边界
    sum = 0
    for i in range(0,img_height):
        y1 = i
        for j in range(0,img_width):
            sum = sum + compareColor(img_array[j,i],bg_color)
        if (sum / img_width) > 2:
            break
    y2 = 0 # 确定下边界
    sum = 0
    for i in range(0,img_height):
        # y2 = img_height - i - 1
        y2 = img_height - i - 1
        for j in range(0,img_width):
            sum = sum + compareColor(img_array[j,y2],bg_color)
        if (sum / img_width) > 2:
            break
    return (x1,y1,x2,y2) # 返回一个矩形坐标


def getGoldBox(img_input,gold_rate = 0.618): # 按黄金分割创建理想留白的矩形
    w = img_input.size[0]
    h = img_input.size[1]
    delta = 4 * ((w + h) ** 2) - 4 * 4 * (w * h - w * h / gold_rate)
    r = int((-2 * (w + h) + math.sqrt(delta)) / 8)
    return [(w + 2 * r),(h + 2 * r),r] # 返回黄金矩形的宽、高、边距

def cropImageByBox(img_input,box_input,bg_color = (255,255,255)): # 从源图像截取一个区域
    r = Image.new('RGBA',((box_input[2] - box_input[0] + 1),(box_input[3] - box_input[1] + 1)),bg_color)
    print('image.new - ok')
    for i in range(0,box_input[2] - box_input[0] + 1): #
        for j in range(0,box_input[3] - box_input[1] + 1): #
            r.putpixel((i,j),img_input.getpixel((i + box_input[0],j + box_input[1])))
    return r

def createCoreImage(img_input):
    r = cropImageByBox(img_input,getCoreBox(img_input))
    return r

def createGoldImage(img_input,bg_color = (255,255,255)): # 创建带有优雅留白边缘的图像
    r = Image.new('RGBA',(getGoldBox(img_input)[0],getGoldBox(img_input)[1]),bg_color)
    for i in range(0,img_input.size[0]):
        for j in range(0,img_input.size[1]):
            r.putpixel((i + getGoldBox(img_input)[2],j + getGoldBox(img_input)[2]),img_input.getpixel((i,j)))
    return r

def putImageIntoBox(img_input,box_width,box_height,fill_mode = 'auto',bg_color = (255,255,255)):

    # 魔法时刻出现了！
    r = Image.new('RGBA',(box_width,box_height),bg_color) # 创建画布
    img_temp = createCoreImage(img_input) # 取原图核心为素材

    # 辨识图片类型
    img_type = 'default' # 默认：核心四周都有留白
    if img_temp.size[0] == img_input.size[0]: # 左右顶边
        img_type = 'full_width'
    if img_temp.size[1] == img_input.size[1]: # 上下顶边
        img_type = 'full_height'
    if (img_temp.size[0] == img_input.size[0]) and (img_temp.size[1] == img_input.size[1]):
        img_type = 'full_all' # 横、纵同时顶边

    rate_box = box_width / box_height # 画布的宽高比
    rate_temp = img_temp.size[0] / img_temp.size[1] # 素材的宽高比

    draw_method = fill_mode # auto, gold, part 可根据参数强制定义
    if draw_method == 'auto': # 若为自动档
        if img_type == 'full_all':
            draw_method = 'part' # 若为满屏图像则取中间局部去塞满整个画框
        elif img_type == 'full_width': # 若素材左右顶边
            if rate_temp < rate_box: # 若素材较窄则取局部，否则为默认 core
                draw_method = 'part'
        elif img_type == 'full_height': # 若素材上下顶边
            if rate_temp > rate_box: # 若素材较宽则取局部，否则为默认 core
                draw_method = 'part'
        elif img_type == 'default': # 若素材正常四周有留白
            draw_method = 'gold' # 取优雅留白的版本

    if draw_method == 'part': # 取中间局部的素材，填满整个画框
        if rate_temp > rate_box: # 若素材较扁，取中间一列
            pix_temp = int(round((img_temp.size[0] - img_temp.size[1] * rate_box) / 2))
            box_temp = (pix_temp,0,img_temp.size[0] - pix_temp - 1,img_temp.size[1] - 1)
            img_temp = cropImageByBox(img_temp,box_temp)
        else: # 若素材较窄，取中间一行
            pix_temp = int(round(img_temp.size[1] - img_temp.size[0] / rate_box) / 2)
            box_temp = (0,pix_temp,img_temp.size[0] - 1,img_temp.size[1] - pix_temp - 1)
            img_temp = cropImageByBox(img_temp,box_temp)
        rate_temp = img_temp.size[0] / img_temp.size[1] # 更新素材的宽高比

    if draw_method == 'gold':
        img_temp = createGoldImage(img_temp) # 四边加黄金留白
        rate_temp = img_temp.size[0] / img_temp.size[1] # 更新素材的宽高比

    draw_point = (0,0) # 画笔初始化

    if rate_temp > rate_box: # 若素材较扁，缩放到与画框等宽
        img_temp = img_temp.resize((box_width,int(round(box_width / rate_temp))),Image.ANTIALIAS)
        draw_point = (0,int(round((box_height - img_temp.size[1]) / 2)))
    else: # 若素材较窄，缩放到与画框等高
        img_temp = img_temp.resize((int(round(box_height * rate_temp)),box_height),Image.ANTIALIAS)
        draw_point = (int(round((box_width - img_temp.size[0]) / 2)),0)

    for i in range(0,img_temp.size[0]): #绘制到画布
        for j in range(0,img_temp.size[1]):
            r.putpixel((draw_point[0] + i,draw_point[1] + j),img_temp.getpixel((i,j)))

    return r

print('imglib.py imported. - ok')
