import PyInstaller.__main__
import os
import shutil

# 确保资源目录存在
if not os.path.exists('dist/resources'):
    os.makedirs('dist/resources')

# 复制资源文件
resource_files = [
    # 字体文件
    ('resources/fonts/MSYH.TTF', 'resources/fonts/'),  # 微软雅黑字体
    ('resources/fonts/SourceHanSansSC-VF.ttf', 'resources/fonts/'),  # 思源黑体
    ('resources/fonts/SourceHanSansHWSC-Bold.otf', 'resources/fonts/'),  # 思源黑体粗体
    
    # 背景图片
    ('resources/backgrounds/grid.png', 'resources/backgrounds/'),  # 网格背景
    ('resources/backgrounds/memo.png', 'resources/backgrounds/'),  # 小红书背景
    ('resources/backgrounds/new.png', 'resources/backgrounds/'),  # 新背景
    ('resources/backgrounds/blank.png', 'resources/backgrounds/'),  # 空白背景
    
    # 图标文件
    ('resources/icon.png', 'resources/'),  # 应用图标
    ('resources/icons/app_icon.icns', 'resources/icons/'),  # Mac图标
    
    # 配置文件
    ('resources/config.json', 'resources/'),  # 配置文件
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
    '--icon=resources/icon.icns',
    '--add-data=resources:resources',
    '--noconfirm',
]) 