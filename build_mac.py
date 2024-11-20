import PyInstaller.__main__
import os
import shutil
import sys
import logging
import traceback

# 设置日志记录
logging.basicConfig(
    filename=os.path.expanduser('~/Desktop/app_error.log'),
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def create_error_handler():
    """创建全局异常处理器"""
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logging.error("Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback))
        
        # 将错误信息写入文件
        with open(os.path.expanduser('~/Desktop/app_crash.txt'), 'w', encoding='utf-8') as f:
            f.write(f"程序发生错误:\n")
            f.write(''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    
    return handle_exception

def build_mac_app():
    """Build macOS application"""
    try:
        print("Starting macOS build process...")
        
        # 设置全局异常处理
        sys.excepthook = create_error_handler()
        
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
            '--name=小红书文字转图片工具mac',  # 应用名称
            '--windowed',  # macOS上创建.app bundle
            '--noconfirm',  # 覆盖现有文件
            '--clean',  # 清理临时文件  
            '--onedir',  # 创建单目录分发
            
            # 使用临时图标
            f'--icon={temp_icon_path}',
            
            # 添加所需的包
            '--hidden-import=PIL',
            '--hidden-import=PyQt6',
            '--hidden-import=aiohttp',
            '--hidden-import=markdown',  # 添加markdown解析模块
            '--hidden-import=ui.markdown_editor',  # 添加markdown编辑器模块
            
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
import logging
import traceback

# 根据操作系统类型设置日志目录
if sys.platform == 'darwin':  # macOS
    log_dir = os.path.expanduser('~/Library/Logs/小红书文字转图片工具')
elif sys.platform == 'win32':  # Windows
    log_dir = os.path.join(os.getenv('APPDATA'), '小红书文字转图片工具', 'logs')
else:  # Linux 或其他系统
    log_dir = os.path.expanduser('~/.小红书文字转图片工具/logs')

# 确保日志目录存在
os.makedirs(log_dir, exist_ok=True)

# 设置日志记录
logging.basicConfig(
    filename=os.path.join(log_dir, 'runtime.log'),
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 设置全局异常处理
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logging.error("Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback))
    
    # 将错误信息写入文件
    with open(os.path.expanduser('~/Desktop/app_crash.txt'), 'w', encoding='utf-8') as f:
        f.write(f"程序发生错误:\\n")
        f.write(''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)))

sys.excepthook = handle_exception

def get_resource_path(relative_path):
    try:
        if getattr(sys, 'frozen', False):
            if hasattr(sys, '_MEIPASS'):
                base_path = sys._MEIPASS
                logging.debug(f"Running from PyInstaller bundle. MEIPASS: {base_path}")
            else:
                base_path = os.path.dirname(sys.executable)
                logging.debug(f"Running from frozen app. Executable dir: {base_path}")
        else:
            base_path = os.path.abspath('.')
            logging.debug(f"Running in development mode. Base path: {base_path}")
            
        full_path = os.path.join(base_path, relative_path)
        logging.debug(f"Full resource path: {full_path}")
        
        if os.path.exists(full_path):
            logging.info(f"Resource exists at: {full_path}")
        else:
            logging.warning(f"Resource not found at: {full_path}")
            
        return full_path
    except Exception as e:
        logging.error(f"Error in get_resource_path: {str(e)}\\n{traceback.format_exc()}")
        return None

try:
    # 设置环境变量以供应用程序使用
    resource_path = get_resource_path('resources')
    if resource_path and os.path.exists(resource_path):
        os.environ['RESOURCE_PATH'] = resource_path
        logging.info(f"Resource path set to: {resource_path}")
        
        # 验证关键资源文件
        for required_file in ['fonts']:
            check_path = os.path.join(resource_path, required_file)
            if os.path.exists(check_path):
                logging.info(f"Found required resource: {required_file}")
            else:
                logging.error(f"Missing required resource: {required_file}")
    else:
        logging.error("Failed to set resource path")
except Exception as e:
    logging.error(f"Error in runtime hook: {str(e)}\\n{traceback.format_exc()}")
""")

        try:
            print("Running PyInstaller...")
            PyInstaller.__main__.run(pyinstaller_args)

            # 复制额外的资源文件到应用包
            print("Copying additional resources...")
            app_path = os.path.join("dist", "小红书文字转图片工具mac.app", "Contents", "MacOS")
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
            print("Application bundle created at: dist/小红书文字转图片工具mac.app")
            print("\nTo run the application:")
            print("1. Open Finder")
            print("2. Navigate to the 'dist' folder")
            print("3. Double click '小红书文字转图片工具mac.app'")

        finally:
            # 清理临时文件
            if os.path.exists(temp_icon_path):
                os.remove(temp_icon_path)
                print("Cleaned up temporary icon file")
            if os.path.exists('runtime_hook.py'):
                os.remove('runtime_hook.py')
                print("Cleaned up runtime hook file")

    except Exception as e:
        logging.error(f"Build error: {str(e)}\n{traceback.format_exc()}")
        raise

if __name__ == "__main__":
    build_mac_app()