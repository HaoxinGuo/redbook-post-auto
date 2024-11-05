import os
import shutil
import PyInstaller.__main__

def clean_build_folders():
    """清理构建文件夹"""
    folders_to_clean = ['build', 'dist']
    for folder in folders_to_clean:
        if os.path.exists(folder):
            shutil.rmtree(folder)
    
    # 清理 spec 文件
    if os.path.exists('xiaohongshu_image_generator.spec'):
        os.remove('xiaohongshu_image_generator.spec')

def copy_resources(dist_path):
    """复制资源文件到打包目录"""
    # Mac应用程序包中的资源目录
    resources_dist = os.path.join(dist_path, 'xiaohongshu_image_generator.app', 
                                'Contents', 'Resources', 'resources')
    os.makedirs(resources_dist, exist_ok=True)
    
    # 复制字体文件
    fonts_src = os.path.join('resources', 'fonts')
    fonts_dist = os.path.join(resources_dist, 'fonts')
    if os.path.exists(fonts_src):
        if os.path.exists(fonts_dist):
            shutil.rmtree(fonts_dist)
        shutil.copytree(fonts_src, fonts_dist)
    
    # 复制背景图片
    backgrounds_src = os.path.join('resources', 'backgrounds')
    backgrounds_dist = os.path.join(resources_dist, 'backgrounds')
    if os.path.exists(backgrounds_src):
        if os.path.exists(backgrounds_dist):
            shutil.rmtree(backgrounds_dist)
        shutil.copytree(backgrounds_src, backgrounds_dist)
    
    # 复制图标
    icons_src = os.path.join('resources', 'icons')
    icons_dist = os.path.join(resources_dist, 'icons')
    if os.path.exists(icons_src):
        if os.path.exists(icons_dist):
            shutil.rmtree(icons_dist)
        shutil.copytree(icons_src, icons_dist)
    
    # 复制配置文件
    config_src = os.path.join('resources', 'config.json')
    if os.path.exists(config_src):
        shutil.copy2(config_src, os.path.join(resources_dist, 'config.json'))

def build_app():
    """构建Mac应用程序"""
    # 清理旧的构建文件
    clean_build_folders()
    
    # 设置打包参数
    args = [
        'main.py',
        '--name=xiaohongshu_image_generator',
        '--windowed',  # macOS GUI 应用
        '--noconfirm',
        '--clean',
        '--add-data=resources:resources',  # macOS 使用冒号分隔
        '--hidden-import=PIL',
        '--hidden-import=PyQt6',
        '--target-architecture=x86_64',  # 支持 Intel 芯片
        '--target-architecture=arm64',   # 支持 M1/M2 芯片
    ]
    
    # 如果有图标文件，添加图标
    if os.path.exists('resources/icons/app_icon.icns'):
        args.append('--icon=resources/icons/app_icon.icns')
    
    # 执行打包
    PyInstaller.__main__.run(args)
    
    # 复制资源文件
    dist_path = os.path.join('dist')
    copy_resources(dist_path)
    
    print("Mac应用程序打包完成！")
    print(f"应用程序位置: {os.path.join(dist_path, 'xiaohongshu_image_generator.app')}")

if __name__ == '__main__':
    build_app() 