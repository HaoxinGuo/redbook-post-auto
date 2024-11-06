import PyInstaller.__main__
import os
import shutil

# 确保资源目录存在
if not os.path.exists('dist/resources'):
    os.makedirs('dist/resources')

# 复制资源文件
resource_files = [
    ('resources/fonts/SourceHanSansSC-VF.ttf', 'resources/fonts/'),
    ('resources/fonts/SourceHanSansHWSC-Bold.otf', 'resources/fonts/'),  # 添加粗体字体
    ('resources/fonts/MSYH.TTF', 'resources/fonts/'),
    ('resources/backgrounds/grid.png', 'resources/backgrounds/'),
    ('resources/backgrounds/dot.png', 'resources/backgrounds/'),
    ('resources/backgrounds/blank.png', 'resources/backgrounds/'),
    ('resources/icon.png', 'resources/'),  # 添加图标文件
]

# 复制所有资源文件
for src, dst in resource_files:
    dst_dir = os.path.join('dist', dst)
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
    shutil.copy2(src, os.path.join('dist', dst))

# 运行PyInstaller
PyInstaller.__main__.run([
    'main.py',
    '--name=小红书文字转图片工具',
    '--windowed',
    '--onefile',
    '--icon=resources/icon.ico',
    '--add-data=resources;resources',
    '--noconfirm',
]) 