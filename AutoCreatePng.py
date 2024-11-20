# -*- coding: utf-8 -*-
"""
Created on Wed Nov 20 14:33:09 2024

@author: NEO
"""

# -*- coding: utf-8 -*-
"""
Created on Wed Nov 20 14:21:53 2024

@author: NEO
"""

from PIL import Image, ImageDraw

# HEX 到 RGB 转换函数
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# 图片生成函数
def generate_grid_image(hex_color, file_name, canvas_width=1080, canvas_height=1440, grid_size=45):
    # 转换 HEX 颜色为 RGB
    background_color_rgb = hex_to_rgb(hex_color)
    line_color = (200, 200, 200)  # Grid line color (light gray)

    # 创建图像
    image = Image.new("RGB", (canvas_width, canvas_height), background_color_rgb)
    draw = ImageDraw.Draw(image)

    # 绘制网格
    for x in range(0, canvas_width, grid_size):
        draw.line([(x, 0), (x, canvas_height)], fill=line_color, width=1)
    for y in range(0, canvas_height, grid_size):
        draw.line([(0, y), (canvas_width, y)], fill=line_color, width=1)

    # 保存图片
    image.save(file_name)
    print(f"Image saved as {file_name}")

# HEX 颜色与文件名的映射
hex_colors_and_names = [
    {"hex_color": "#F2F2F2", "file_name": "lightgray.png"},
    {"hex_color": "#F8F8F0", "file_name": "beige.png"},
    {"hex_color": "#FFFFFF", "file_name": "white.png"},
    {"hex_color": "#FFF9E6", "file_name": "yellowish.png"},
    {"hex_color": "#FFF0F5", "file_name": "pinkish.png"},
    {"hex_color": "#E8F6FF", "file_name": "lightblue.png"},
]

# 循环生成图片
for item in hex_colors_and_names:
    generate_grid_image(item["hex_color"], f"C:/Users/jaspe/OneDrive/小红书/redbook-post-auto/resources/backgrounds/{item['file_name']}")
