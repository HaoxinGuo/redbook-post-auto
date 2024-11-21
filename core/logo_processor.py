from PIL import Image
import os
import sys
import logging
import traceback

class LogoProcessor:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.logger = logging.getLogger('LogoProcessor')
        self.logger.propagate = False
        
        if not self.logger.handlers:
            self.logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(levelname)s - %(message)s')
            
            if sys.platform == 'darwin':  # macOS
                log_dir = os.path.expanduser('~/Library/Logs/小红书文字转图片工具')
            elif sys.platform == 'win32':  # Windows
                log_dir = os.path.join(os.getenv('APPDATA'), '小红书文字转图片工具', 'logs')
            else:  # Linux 或其他系统
                log_dir = os.path.expanduser('~/.小红书文字转图片工具/logs')
            
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, 'app.log')
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def add_logo(self, images):
        """为图片添加Logo"""
        try:
            # 获取 logo 路径
            if hasattr(sys, '_MEIPASS'):
                logo_path = os.path.join(sys._MEIPASS, 'resources', 'icons', 'logo.png')
            else:
                logo_path = os.path.join('resources', 'icons', 'logo.png')
            
            self.logger.info("\n=== 添加 Logo ===")
            self.logger.info(f"Logo 路径: {logo_path}")
            self.logger.info(f"Logo 文件是否存在: {os.path.exists(logo_path)}")
            
            if os.path.exists(logo_path):
                # 加载并处理logo
                with Image.open(logo_path) as logo:
                    # 确保logo是RGBA模式
                    logo = logo.convert('RGBA')
                    self.logger.debug(f"Logo 模式: {logo.mode}")
                    self.logger.debug(f"原始 Logo 尺寸: {logo.size}")
                    
                    # 调整logo大小
                    logo_height = 50  # 增大logo尺寸
                    aspect_ratio = logo.width / logo.height
                    logo_width = int(logo_height * aspect_ratio)
                    logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
                    self.logger.debug(f"调整后的 Logo 尺寸: {logo.size}")
                    
                    # 计算位置
                    margin = 20
                    x = margin
                    y = self.height - logo_height - margin
                    self.logger.debug(f"Logo 位置: ({x}, {y})")
                    
                    # 为每个图片添加logo
                    for i, image in enumerate(images):
                        try:
                            # 创建新的图片副本
                            new_image = image.copy()
                            new_image = new_image.convert('RGBA')
                            
                            # 创建透明图层
                            overlay = Image.new('RGBA', new_image.size, (0, 0, 0, 0))
                            overlay.paste(logo, (x, y), logo)
                            
                            # 合并图层
                            result = Image.alpha_composite(new_image, overlay)
                            images[i] = result.convert('RGB')
                            
                            self.logger.debug(f"成功添加Logo到第 {i+1} 张图片")
                        except Exception as e:
                            self.logger.error(f"处理第 {i+1} 张图片时出错: {str(e)}")
                            self.logger.error(traceback.format_exc())
                            continue
                    
                    self.logger.info("Logo 添加成功")
            else:
                self.logger.warning(f"Logo 文件不存在: {logo_path}")
                
        except Exception as e:
            self.logger.error(f"添加 Logo 失败: {str(e)}")
            self.logger.error(traceback.format_exc()) 