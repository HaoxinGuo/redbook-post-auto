import PyInstaller.__main__
import os
import shutil
import sys

def check_resource_exists(path):
    """检查资源文件是否存在"""
    if not os.path.exists(path):
        print(f"错误: 找不到资源文件 {path}")
        return False
    return True

# 确保资源目录存在
if not os.path.exists('dist/resources'):
    os.makedirs('dist/resources')

# 定义资源文件列表
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
    ('resources/icons/app_icon.ico', 'resources/icons/'),  # Windows图标
    
    # 配置文件
    ('resources/config.json', 'resources/'),  # 配置文件
]

# 检查所有资源文件是否存在
missing_files = False
for src, _ in resource_files:
    if not check_resource_exists(src):
        missing_files = True

if missing_files:
    print("\n请确保以下目录结构和文件存在:")
    print("resources/")
    print("├── fonts/")
    print("│   ├── MSYH.TTF")
    print("│   ├── SourceHanSansSC-VF.ttf")
    print("│   └── SourceHanSansHWSC-Bold.otf")
    print("├── backgrounds/")
    print("│   ├── grid.png")
    print("│   ├── dot.png")
    print("│   └── blank.png")
    print("└── icon.png")
    sys.exit(1)

# 复制所有资源文件
try:
    for src, dst in resource_files:
        dst_dir = os.path.join('dist', dst)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        print(f"复制文件: {src} -> {os.path.join('dist', dst)}")
        shutil.copy2(src, os.path.join('dist', dst))
except Exception as e:
    print(f"复制资源文件时出错: {str(e)}")
    sys.exit(1)

print("资源文件复制完成，开始打包...")

# 运行PyInstaller
try:
    PyInstaller.__main__.run([
        'main.py',
        '--name=小红书文字转图片工具',
        '--windowed',
        '--onefile',
        '--icon=resources/icons/app_icon.ico',
        '--add-data=resources;resources',
        '--noconfirm',
    ])
    print("打包完成!")
except Exception as e:
    print(f"打包过程出错: {str(e)}")
    sys.exit(1) 