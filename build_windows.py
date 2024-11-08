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

print("开始打包...")

# 运行PyInstaller
try:
    PyInstaller.__main__.run([
        'main.py',
        '--name=小红书文字转图片工具',
        '--windowed',
        '--icon=resources/icons/app_icon.ico',
        '--add-data=resources;resources',  # 确保资源文件被包含
        '--hidden-import=PyQt6.QtCore',
        '--hidden-import=PyQt6.QtGui',
        '--hidden-import=PyQt6.QtWidgets',
        '--hidden-import=ui.styles',
        '--hidden-import=ui.style_text_editor',
        '--hidden-import=PIL',
        '--clean',
        '--noconfirm',
    ])
    print("PyInstaller 打包完成!")

    # 获取目标目录路径
    dist_dir = os.path.join("dist", "小红书文字转图片工具")
    
    # 确保目标目录存在
    if not os.path.exists(dist_dir):
        print(f"错误: 找不到生成的应用程序目录 {dist_dir}")
        sys.exit(1)

    print("\n开始复制资源文件...")
    
    # 复制资源文件到目标目录
    for src, dst in resource_files:
        dst_dir = os.path.join(dist_dir, dst)
        # 确保目标目录存在
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        dst_path = os.path.join(dst_dir, os.path.basename(src))
        print(f"复制: {src} -> {dst_path}")
        try:
            shutil.copy2(src, dst_path)
        except Exception as e:
            print(f"复制文件失败 {src}: {str(e)}")
            sys.exit(1)

    print("资源文件复制完成!")

    # 创建发布目录
    release_dir = "release"
    if not os.path.exists(release_dir):
        os.makedirs(release_dir)

    # 复制整个dist目录到发布目录
    release_path = os.path.join(release_dir, "小红书文字转图片工具")
    if os.path.exists(release_path):
        shutil.rmtree(release_path)
    shutil.copytree(dist_dir, release_path)
    print(f"\n应用程序已复制到: {release_path}")

except Exception as e:
    print(f"打包过程出错: {str(e)}")
    sys.exit(1)

print("\n打包完成! 生成的文件在 release 目录中")