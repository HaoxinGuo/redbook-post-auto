import PyInstaller.__main__
import os
import shutil
import sys
import logging
from pathlib import Path

def setup_logger():
    """设置日志记录器"""
    try:
        # 设置日志目录
        log_dir = os.path.join(os.getenv('APPDATA'), '小红书文字转图片工具', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # 设置日志文件路径
        log_file = os.path.join(log_dir, 'build.log')
        
        # 配置日志记录
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()  # 同时输出到控制台
            ]
        )
        
        return logging.getLogger('BuildScript')
        
    except Exception as e:
        print(f"Error setting up logger: {str(e)}")
        # 如果无法设置文件日志，至少设置控制台日志
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
        return logging.getLogger('BuildScript')

def check_resource_exists(path, logger):
    """检查资源文件是否存在"""
    if not os.path.exists(path):
        logger.error(f"错误: 找不到资源文件 {path}")
        return False
    return True

def create_resource_list(logger):
    """创建资源文件列表"""
    resources_dir = Path('resources')
    resource_files = []
    
    # 遍历resources目录下的所有文件
    for file_path in resources_dir.rglob('*'):
        if file_path.is_file():
            # 获取相对于resources的路径
            relative_path = file_path.relative_to(resources_dir)
            # 创建目标路径（保持目录结构）
            target_dir = os.path.join('resources', str(relative_path.parent))
            # 添加到资源列表
            resource_files.append((str(file_path), target_dir))
            logger.debug(f"添加资源文件: {file_path} -> {target_dir}")
    
    return resource_files

def main():
    # 设置日志记录器
    logger = setup_logger()
    logger.info("=== 开始打包程序 ===")
    
    try:
        # 获取所有资源文件
        resource_files = create_resource_list(logger)
        
        # 检查资源文件是否存在
        missing_files = False
        for src, _ in resource_files:
            if not check_resource_exists(src, logger):
                missing_files = True
        
        if missing_files:
            logger.error("\n错误：缺少必要的资源文件")
            logger.error("请确保resources目录包含所有必要文件")
            sys.exit(1)
        
        # 准备PyInstaller参数
        pyinstaller_args = [
            'main.py',
            '--name=小红书文字转图片工具',
            '--windowed',
            '--icon=resources/icons/app_icon.ico',
            '--add-data=resources;resources',
            '--hidden-import=PyQt6.QtCore',
            '--hidden-import=PyQt6.QtGui',
            '--hidden-import=PyQt6.QtWidgets',
            '--hidden-import=ui.styles',
            '--hidden-import=ui.style_text_editor',
            '--hidden-import=ui.markdown_editor',
            '--hidden-import=markdown',
            '--hidden-import=PIL',
            '--clean',
            '--noconfirm',
            '--noupx',
            '--noconsole',
            '--optimize=2',
            '--log-level=WARN',
        ]
        
        logger.info("\n1. 开始PyInstaller打包...")
        PyInstaller.__main__.run(pyinstaller_args)
        logger.info("PyInstaller打包完成!")
        
        # 获取生成的目录路径
        dist_dir = Path("dist") / "小红书文字转图片工具"
        
        if not dist_dir.exists():
            raise FileNotFoundError(f"找不到生成的应用程序目录: {dist_dir}")
        
        logger.info("\n2. 开始复制资源文件...")
        # 复制资源文件到目标目录
        for src, dst in resource_files:
            dst_dir = dist_dir / dst
            dst_dir.mkdir(parents=True, exist_ok=True)
            dst_path = dst_dir / Path(src).name
            
            logger.info(f"复制: {src} -> {dst_path}")
            try:
                shutil.copy2(src, dst_path)
            except Exception as e:
                logger.warning(f"警告: 复制文件失败 {src}: {str(e)}")
        
        logger.info("资源文件复制完成!")
        
        # 清理临时文件和目录
        logger.info("\n4. 清理临时文件...")
        if Path("build").exists():
            shutil.rmtree("build")
        for file in Path(".").glob("*.spec"):
            file.unlink()
        
        logger.info("\n=== 打包完成! ===")
        logger.info(f"生成的文件在: {dist_dir}")
        logger.info("\n提示：")
        logger.info("1. 请检查dist目录中的程序是否可以正常运行")
        logger.info("2. 确保所有资源文件都已正确包含")
        logger.info("3. 如果运行出现问题，请查看是否缺少必要的DLL文件")
        
    except Exception as e:
        logger.error(f"\n错误: 打包过程出错")
        logger.error(f"详细信息: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()