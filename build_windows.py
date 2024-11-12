import PyInstaller.__main__
import os
import shutil
import sys
from pathlib import Path

def check_resource_exists(path):
    """检查资源文件是否存在"""
    if not os.path.exists(path):
        print(f"错误: 找不到资源文件 {path}")
        return False
    return True

def create_resource_list():
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
    
    return resource_files

def main():
    print("=== 开始打包程序 ===")
    
    # 获取所有资源文件
    resource_files = create_resource_list()
    
    # 检查资源文件是否存在
    missing_files = False
    for src, _ in resource_files:
        if not check_resource_exists(src):
            missing_files = True
    
    if missing_files:
        print("\n错误：缺少必要的资源文件")
        print("请确保resources目录包含所有必要文件")
        sys.exit(1)
    
    # 准备PyInstaller参数
    pyinstaller_args = [
        'main.py',
        '--name=小红书文字转图片工具',
        '--windowed',  # 无控制台窗口
        '--icon=resources/icons/app_icon.ico',
        '--add-data=resources;resources',  # 添加整个resources目录
        '--hidden-import=PyQt6.QtCore',
        '--hidden-import=PyQt6.QtGui',
        '--hidden-import=PyQt6.QtWidgets',
        '--hidden-import=ui.styles',
        '--hidden-import=ui.style_text_editor',
        '--hidden-import=PIL',
        '--clean',  # 清理临时文件
        '--noconfirm',  # 不确认覆盖
        '--noupx',  # 不使用UPX压缩
        '--noconsole',  # 不显示控制台
        # 优化选项
        '--optimize=2',  # 应用优化
        '--log-level=WARN',  # 只显示警告和错误
    ]
    
    try:
        print("\n1. 开始PyInstaller打包...")
        PyInstaller.__main__.run(pyinstaller_args)
        print("PyInstaller打包完成!")
        
        # 获取生成的目录路径
        dist_dir = Path("dist") / "小红书文字转图片工具"
        
        if not dist_dir.exists():
            raise FileNotFoundError(f"找不到生成的应用程序目录: {dist_dir}")
        
        print("\n2. 开始复制资源文件...")
        # 复制资源文件到目标目录
        for src, dst in resource_files:
            dst_dir = dist_dir / dst
            dst_dir.mkdir(parents=True, exist_ok=True)
            dst_path = dst_dir / Path(src).name
            
            print(f"复制: {src} -> {dst_path}")
            try:
                shutil.copy2(src, dst_path)
            except Exception as e:
                print(f"警告: 复制文件失败 {src}: {str(e)}")
                # 继续执行，而不是立即退出
        
        print("资源文件复制完成!")
        
        # 清理临时文件和目录
        print("\n4. 清理临时文件...")
        if Path("build").exists():
            shutil.rmtree("build")
        for file in Path(".").glob("*.spec"):
            file.unlink()
        
        print("\n=== 打包完成! ===")
        print(f"生成的文件在: {dist_dir}")
        print("\n提示：")
        print("1. 请检查dist目录中的程序是否可以正常运行")
        print("2. 确保所有资源文件都已正确包含")
        print("3. 如果运行出现问题，请查看是否缺少必要的DLL文件")
        
    except Exception as e:
        print(f"\n错误: 打包过程出错")
        print(f"详细信息: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()