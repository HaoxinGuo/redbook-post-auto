import PyInstaller.__main__
import os
import shutil
import pkg_resources

def build_mac_app():
    """Build macOS application"""
    print("Starting macOS build process...")

    # 清理之前的构建文件
    print("Cleaning previous build files...")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")

    # 确保资源目录存在
    if not os.path.exists("resources"):
        print("Error: resources directory not found!")
        return

    # 创建临时图标文件
    print("Creating temporary icon file...")
    temp_icon_path = os.path.join("resources", "temp_icon.icns")
    if not os.path.exists(temp_icon_path):
        # 创建一个空的icns文件
        with open(temp_icon_path, 'wb') as f:
            f.write(b'icns')

    # PyInstaller 参数
    pyinstaller_args = [
        'main.py',  # 主程序文件
        '--name=小红书文字转图片工具',  # 应用名称
        '--windowed',  # macOS上创建.app bundle
        '--noconfirm',  # 覆盖现有文件
        '--clean',  # 清理临时文��
        '--onedir',  # 创建单目录分发
        
        # 使用临时图标
        f'--icon={temp_icon_path}',
        
        # 添加所需的包
        '--hidden-import=PIL',
        '--hidden-import=PyQt6',
        '--hidden-import=aiohttp',
        
        # 添加资源文件
        '--add-data=resources:resources',
        '--add-data=resources/fonts:resources/fonts',  # 特别添加字体文件
        
        # 排除不需要的模块
        '--exclude-module=matplotlib',
        '--exclude-module=numpy',
        '--exclude-module=pandas',
        
        # 其他优化选项
        '--noupx',  # 不使用UPX压缩
        
        # 添加运行时钩子
        '--runtime-hook=runtime_hook.py',
    ]

    # 创建运行时钩子文件
    print("Creating runtime hook...")
    with open('runtime_hook.py', 'w', encoding='utf-8') as f:
        f.write("""
import os
import sys

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)

# 设置环境变量以供应用程序使用
os.environ['RESOURCE_PATH'] = get_resource_path('resources')

# 打印资源路径信息用于调试
print(f"Resource path set to: {os.environ['RESOURCE_PATH']}")
if hasattr(sys, '_MEIPASS'):
    print(f"Running from PyInstaller bundle. MEIPASS: {sys._MEIPASS}")
    print(f"Contents of MEIPASS:")
    for root, dirs, files in os.walk(sys._MEIPASS):
        print(f"Directory: {root}")
        for d in dirs:
            print(f"  Dir: {d}")
        for f in files:
            print(f"  File: {f}")
""")

    try:
        print("Running PyInstaller...")
        PyInstaller.__main__.run(pyinstaller_args)

        # 复制额外的资源文件到应用包
        print("Copying additional resources...")
        app_path = os.path.join("dist", "小红书文字转图片工具.app", "Contents", "MacOS")
        resources_path = os.path.join(app_path, "resources")
        
        # 确保目标资源目录存在
        os.makedirs(resources_path, exist_ok=True)
        
        # 复制资源文件
        if os.path.exists("resources"):
            print(f"Copying resources from {os.path.abspath('resources')} to {resources_path}")
            for item in os.listdir("resources"):
                if item == "temp_icon.icns":  # 跳过临时图标文件
                    continue
                source = os.path.join("resources", item)
                destination = os.path.join(resources_path, item)
                print(f"Copying {source} to {destination}")
                try:
                    if os.path.isdir(source):
                        if os.path.exists(destination):
                            shutil.rmtree(destination)
                        shutil.copytree(source, destination)
                        print(f"Copied directory: {item}")
                    else:
                        shutil.copy2(source, destination)
                        print(f"Copied file: {item}")
                except Exception as e:
                    print(f"Error copying {item}: {str(e)}")

        print("\nBuild completed!")
        print("Application bundle created at: dist/小红书文字转图片工具.app")
        print("\nTo run the application:")
        print("1. Open Finder")
        print("2. Navigate to the 'dist' folder")
        print("3. Double click '小红书文字转图片工具.app'")

    finally:
        # 清理临时文件
        if os.path.exists(temp_icon_path):
            os.remove(temp_icon_path)
            print("Cleaned up temporary icon file")
        if os.path.exists('runtime_hook.py'):
            os.remove('runtime_hook.py')
            print("Cleaned up runtime hook file")

if __name__ == "__main__":
    build_mac_app()