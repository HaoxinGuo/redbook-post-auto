from PIL import Image, ImageDraw, ImageFont
import os
import textwrap
import re
import sys
import logging
from datetime import datetime
from core.logo_processor import LogoProcessor

class ImageGenerator:
    """
    图片生成器类
    负责将文本内容转换为图片，支持标题、正文、列表等多种格式的渲染
    """
    def __init__(self):
        """
        初始化图片生成器
        设置基本参数、初始化日志系统和字体加载
        """
        self.width = 1080        # 图片宽度
        self.height = 1440       # 图片高度 (3:4 比例)
        self.margin = 50         # 页面边距
        self.list_indent = 30    # 列表缩进
        self.logo_processor = LogoProcessor(self.width, self.height)
        
        # 设置日志和加载字体
        self.setup_logger()
        self.fonts = self.load_fonts()
        
    def setup_logger(self):
        """设置日志记录器"""
        try:
            # 获取logger
            self.logger = logging.getLogger('ImageGenerator')
            # 避免日志向上层传递
            self.logger.propagate = False
            
            # 只在没有处理器时添加处理器
            if not self.logger.handlers:
                self.logger.setLevel(logging.DEBUG)
                formatter = logging.Formatter('%(levelname)s - %(message)s')
                
                # 根据操作系统类型设置日志目录
                if sys.platform == 'darwin':  # macOS
                    log_dir = os.path.expanduser('~/Library/Logs/小红书文字转图片工具')
                elif sys.platform == 'win32':  # Windows
                    log_dir = os.path.join(os.getenv('APPDATA'), '小红书文字转图片工具', 'logs')
                else:  # Linux 或其他系统
                    log_dir = os.path.expanduser('~/.小红书文字转图片工具/logs')
                
                # 确保日志目录存在
                os.makedirs(log_dir, exist_ok=True)
                
                # 设置日志文件路径
                log_file = os.path.join(log_dir, 'app.log')
                
                # 添加文件处理器
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
                
            self.logger.info('Logger initialized')
            
        except Exception as e:
            print(f"Error setting up logger: {str(e)}")
        
    def load_fonts(self):
        """
        加载字体文件
        - 支持打包后和开发环境的字体路径
        - 加载默认字体文件 MSYH.TTF
        
        返回:
            dict: 包含加载好的字体对象的字典
        
        异常:
            - 记录字体加载失败的错误
            - 返回空字典作为降级处理
        """
        fonts = {}
        try:
            # 获取资源路径
            if hasattr(sys, '_MEIPASS'):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.abspath('.')
            
            fonts_dir = os.path.join(base_path, 'resources', 'fonts')
            font_path = os.path.join(fonts_dir, 'MSYH.TTF')
            # 加载手写字体（例如：SourceHanSerif-Regular.otf）
            handwritten_font_path = os.path.join(fonts_dir, 'ZhanKuKuaiLeTi2016XiuDingBan-1.ttf')
            
            if not os.path.exists(font_path):
                self.logger.error(f"Font file not found at: {font_path}")
                raise FileNotFoundError(f"Font file not found: {font_path}")
            if not os.path.exists(handwritten_font_path):
                self.logger.error(f"Handwritten font file not found at: {handwritten_font_path}")
                raise FileNotFoundError(f"Font file not found: {handwritten_font_path}")

                
            fonts['normal'] = ImageFont.truetype(font_path, 32)
            fonts['handwritten'] = ImageFont.truetype(handwritten_font_path, 32)
            self.logger.info("Fonts loaded successfully")
            return fonts
        except Exception as e:
            self.logger.error(f"Error loading fonts: {str(e)}")
            return {}
        
    def create_images(self, text_content, background_path, font_style='normal'):
        """生成图片"""
        try:
            images = []
            remaining_content = text_content.copy()
            page_count = 0
            
            print("\n=== 开始生成图片 ===")
            print(f"总内容块数量: {len(text_content)}")
            print(f"图片尺寸: {self.width}x{self.height}, 边距: {self.margin}")
            
            while remaining_content and page_count < 100:
                page_count += 1
                print(f"\n=== 开始处理第 {page_count} 页 ===")
                
                # 创建新页面
                image = Image.new('RGB', (self.width, self.height), 'white')
                if background_path:
                    try:
                        bg = Image.open(background_path)
                        bg = bg.resize((self.width, self.height))
                        image.paste(bg, (0, 0))
                        print("背景加载成功")
                    except Exception as e:
                        print(f"背景加载失败: {str(e)}")
                
                draw = ImageDraw.Draw(image)
                current_page_content = []
                current_y = self.margin
                max_y = self.height - self.margin * 3
                
                print(f"页面初始Y坐标: {current_y}")
                print(f"页面最大可用Y坐标: {max_y}")
                
                while remaining_content and current_y < max_y:
                    current_item = remaining_content[0]
                    print(f"\n--- 处理内容块 ---")
                    print(f"内容类型: {current_item['type']}")
                    print(f"当前Y坐标: {current_y}")
                    print(f"剩余空间: {max_y - current_y}")
                    
                    # 获取或创建换行后的文本
                    if 'wrapped_lines' not in current_item:
                        try:
                            current_font = ImageFont.truetype(
                                self.fonts[font_style].path,
                                current_item.get('font_size', 48 if current_item['type'] == 'title' else 32)
                            )
                            current_item['wrapped_lines'] = self.get_wrapped_text(
                                current_item['text'],
                                current_font,
                                self.width - (self.margin * 2)
                            )
                            print(f"文本换行处理完成，共 {len(current_item['wrapped_lines'])} 行")
                        except Exception as e:
                            print(f"字体处理失败: {str(e)}")
                            remaining_content.pop(0)
                            continue

                    # 计算当前内容块需要的高度
                    line_spacing = current_item.get('line_spacing', 45)
                    total_height = 0
                    for line in current_item['wrapped_lines']:
                        total_height += line_spacing if line['text'].strip() else line_spacing // 2
                    
                    print(f"当前内容块需要高度: {total_height}")
                    print(f"当前页面剩余高度: {max_y - current_y}")
                    
                    # 判断是否需要分页
                    if current_y + total_height > max_y:
                        # 计算可以放入多少行
                        available_height = max_y - current_y
                        lines_that_fit = 0
                        height_used = 0
                        
                        for line in current_item['wrapped_lines']:
                            next_line_height = line_spacing if line['text'].strip() else line_spacing // 2
                            if height_used + next_line_height <= available_height:
                                lines_that_fit += 1
                                height_used += next_line_height
                            else:
                                break
                        
                        print(f"可以放入 {lines_that_fit} 行，使用高度 {height_used}")
                        
                        if lines_that_fit > 0:
                            # 分割内容
                            page_item = dict(current_item)
                            page_item['wrapped_lines'] = current_item['wrapped_lines'][:lines_that_fit]
                            
                            # 调整颜色信息
                            if 'colors' in current_item:
                                total_chars = sum(len(line['text']) + 1 for line in page_item['wrapped_lines'])
                                page_item['colors'] = self.adjust_color_info(current_item['colors'], 0, total_chars)
                            
                            current_page_content.append(page_item)
                            current_y += height_used
                            
                            # 更新剩余内容
                            remaining_item = dict(current_item)
                            remaining_item['wrapped_lines'] = current_item['wrapped_lines'][lines_that_fit:]
                            
                            # 调整剩余内容的颜色信息
                            if 'colors' in current_item:
                                total_chars_processed = sum(len(line['text']) + 1 for line in current_item['wrapped_lines'][:lines_that_fit])
                                remaining_item['colors'] = self.adjust_color_info(
                                    current_item['colors'],
                                    total_chars_processed,
                                    float('inf')
                                )
                            
                            remaining_content[0] = remaining_item
                            print(f"内容已分割：当前页 {lines_that_fit} 行，剩余 {len(remaining_item['wrapped_lines'])} 行")
                        break
                    else:
                        # 如果内容可以完全放入当前页面
                        current_page_content.append(current_item)
                        current_y += total_height
                        remaining_content.pop(0)
                        print(f"内容块已添加到当前页面，更新Y坐标到: {current_y}")
                
                # 渲染当前页面的内容
                if current_page_content:
                    print(f"\n=== 渲染第 {len(images) + 1} 页 ===")
                    print(f"页面内容块数: {len(current_page_content)}")
                    self.render_text(draw, current_page_content, self.fonts[font_style])
                    images.append(image)
                    print(f"页面渲染完成，当前总页数: {len(images)}")
                
                print(f"剩余未处理内容块数量: {len(remaining_content)}")
            
            print(f"\n=== 图片生成完成 ===")
            print(f"总生成页数: {len(images)}")
            return images
            
        except Exception as e:
            print(f"生成图片错误: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def calculate_content_height(self, content_items, font):
        """计算内容块的总高度"""
        total_height = 0
        for item in content_items:
            if not item.get('text', '').strip():
                continue
                
            # 使内容块自带的字体大小
            font_size = item.get('font_size', 48 if item['type'] == 'title' else 32)
            line_spacing = item.get('line_spacing', 60 if item['type'] == 'title' else 45)
            
            try:
                current_font = ImageFont.truetype(font.path, font_size)
            except Exception as e:
                print(f"调整字体大小失败: {str(e)}")
                continue
            
            # 获取换行后的本
            lines = self.get_wrapped_text(item['text'], current_font, self.width - (self.margin * 2))
            
            # 计算此内容块的高度
            block_height = len(lines) * line_spacing
            block_height += line_spacing // 2  # 添加块间距
            
            total_height += block_height
        
        return total_height
    
    def split_content_block(self, content_block, font, available_height):
        """将内容块分割成两部分，以适应可用高度"""
        if not content_block.get('text', '').strip():
            return None, None
            
        # 使用内容块自带的字体大小
        font_size = content_block.get('font_size', 
                                    48 if content_block['type'] == 'title' else 32)
        line_spacing = content_block.get('line_spacing', 
                                       60 if content_block['type'] == 'title' else 45)
        
        try:
            current_font = ImageFont.truetype(font.path, font_size)
        except Exception as e:
            print(f"调整字体大小失败: {str(e)}")
            return None, None
        
        # 获取换行后的文本
        lines = self.get_wrapped_text(content_block['text'], current_font, self.width - (self.margin * 2))
        
        # 计算可以放入当前页面的行数
        max_lines = int(available_height / line_spacing)
        
        if max_lines <= 0:
            return None, content_block
        
        if max_lines >= len(lines):
            return content_block, None
        
        # 分割文本
        first_part_text = '\n'.join(lines[:max_lines])
        second_part_text = '\n'.join(lines[max_lines:])
        
        # 创建两个新的内容块
        first_part = dict(content_block)
        first_part['text'] = first_part_text
        
        second_part = dict(content_block)
        second_part['text'] = second_part_text
        
        return first_part, second_part
    
    def calculate_lines_per_height(self, height, content_type):
        """计算定高度可以容纳多少行文本"""
        if content_type == 'title':
            line_spacing = 60
            return int(height / line_spacing)
        else:
            line_spacing = 45
            return int(height / line_spacing)
    
    def split_text_by_lines(self, text, font, max_lines, content_type):
        """将按行数分割"""
        if not text.strip():
            return None, None
            
        max_width = self.width - (self.margin * 2)
        
        # 设置字体大小
        if content_type == 'title':
            font_size = 48
        else:
            font_size = 32
            
        try:
            current_font = ImageFont.truetype(font.path, font_size)
        except Exception as e:
            print(f"调整字体大小失败: {str(e)}")
            return None, None
        
        lines = self.get_wrapped_text(text, current_font, max_width)
        
        if len(lines) <= max_lines:
            return text, None
        
        first_part_lines = lines[:max_lines]
        second_part_lines = lines[max_lines:]
        
        # 重合文本，确保去除首尾白
        first_part = '\n'.join(first_part_lines).strip()
        second_part = '\n'.join(second_part_lines).strip()
        
        # 如果分割后的部分为空，回None
        if not first_part:
            first_part = None
        if not second_part:
            second_part = None
            
        return first_part, second_part
    
    def create_single_image(self, text_content, background_path, font_style='normal'):
        """创建单个图片"""
        print("\n=== 开始创建图片 ===")
        print(f"文本: {text_content.get('text', '')[:50]}...")  # 只印前50个符
        print(f"字体大小: {text_content.get('font_size', 48)}")
        print(f"是否加粗: {text_content.get('font_bold', False)}")
        
        # 创建基础图片
        image = Image.new('RGB', (self.width, self.height), 'white')
        
        # 加载背景
        if background_path:
            try:
                bg = Image.open(background_path)
                bg = bg.resize((self.width, self.height))
                image.paste(bg, (0, 0))
                print(f"背景图片加载成功: {background_path}")
            except Exception as e:
                print(f"加载背景图片失败: {str(e)}")
        
        # 创建绘图对象
        draw = ImageDraw.Draw(image)
        
        # 获取内容
        text = text_content.get('text', '')
        font_size = text_content.get('font_size', 48)
        line_spacing = text_content.get('line_spacing', 20)
        char_spacing = text_content.get('char_spacing', 0)
        marks = text_content.get('marks', {})
        is_bold = text_content.get('font_bold', False)  # 获取加粗设置
        
        print("\n=== 文本渲染参数 ===")
        print(f"行间距: {line_spacing}")
        print(f"字间距: {char_spacing}")
        print(f"样式标记数: {len(marks)}")
        
        # 创建字体象，传入加粗参数
        font = self.create_font(font_size, is_bold)
        print(f"体对象创建结果: {font}")
        
        # 绘制文字
        self.draw_styled_text(
            draw,
            text,
            marks,
            0,
            0,
            font,
            char_spacing=char_spacing,
            line_spacing=line_spacing
        )
        
        # 添加 logo
        try:
            # 获取 logo 路径
            if hasattr(sys, '_MEIPASS'):
                logo_path = os.path.join(sys._MEIPASS, 'resources/icons', 'logo.png')
            else:
                logo_path = os.path.join('resources/icons', 'logo.png')
            
            print(f"Logo 路径: {logo_path}")
            print(f"Logo 文件是否存在: {os.path.exists(logo_path)}")
            
            if os.path.exists(logo_path):
                # 加载 logo
                logo = Image.open(logo_path)
                print(f"Logo 模式: {logo.mode}")
                print(f"Logo 尺寸: {logo.size}")
                
                # 设置 logo 大小（可以调整这个值来改变 logo 大小
                logo_height = 60  # logo 的目标高度
                aspect_ratio = logo.width / logo.height
                logo_width = int(logo_height * aspect_ratio)
                
                # 调整 logo 大小
                logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
                print(f"调整后的 Logo 尺寸: {logo.size}")
                
                # 计算 logo 置（左下角，留边距）
                margin = 40  # 边距
                x = margin
                y = self.height - logo_height - margin
                print(f"Logo 位置: ({x}, {y})")
                
                # 果 logo 有透明通道，需要特殊处理
                if logo.mode == 'RGBA':
                    print("处理带透明通道的 Logo")
                    # 将图转换为 RGBA 模式
                    image = image.convert('RGBA')
                    # 创建一个与原图大小相的透明图层
                    overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
                    # 将 logo 粘贴到透明图层上
                    overlay.paste(logo, (x, y))
                    # 将透明图层与原图合并
                    image = Image.alpha_composite(image, overlay)
                    # 转换回 RGB 模式
                    image = image.convert('RGB')
                else:
                    print("处理不带透明通道的 Logo")
                    # 如果 logo 没有透明通道，直接粘贴
                    image.paste(logo, (x, y))
                    
                print("Logo 添加成功")
            else:
                print(f"Logo 文件不存在: {logo_path}")
                
        except Exception as e:
            print(f"添加 Logo 失败: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("=== 图片创建完成 ===\n")
        return image
    
    def process_list_text(self, text):
        """处理文本中的列表"""
        lines = text.split('\n')
        processed_lines = []
        list_stack = []  # 用于跟踪嵌套列表
        
        # 扩展列表标记正则表达式
        ordered_patterns = [
            r'(\d+)[.、)]\s+(.+)',  # 数字列表：1. 1、 1)
            r'([a-z])[.、)]\s+(.+)',  # 字母列表：a. a、 a)
            r'([A-Z])[.、)]\s+(.+)'  # 大写字母列表：A. A、 A)
        ]
        unordered_patterns = [
            r'[-•*]\s+(.+)',        # 常规无序列表标记
            r'[○◆◇]\s+(.+)'      # 其他无序列表标记
        ]
        
        def get_indent_level(line):
            """获取缩进级别"""
            return len(line) - len(line.lstrip())
        
        def is_ordered_list(line):
            """检查是否是有列表项"""
            for pattern in ordered_patterns:
                match = re.match(pattern, line.lstrip())
                if match:
                    return match
            return None
        
        def is_unordered_list(line):
            """检查是否是无序列表项"""
            for pattern in unordered_patterns:
                match = re.match(pattern, line.lstrip())
                if match:
                    return match
            return None
        
        # 用于跟踪每个缩进级别的编号
        current_list_number = {}
        
        for line in lines:
            if not line.strip():
                processed_lines.append('')
                continue
            
            indent_level = get_indent_level(line)
            stripped_line = line.lstrip()
            
            # 检查是否是有序列表
            ordered_match = is_ordered_list(stripped_line)
            if ordered_match:
                marker, content = ordered_match.groups()
                
                # 计算实际缩进
                indent_spaces = self.list_indent * (indent_level + 1)  # 基础缩进加上层级缩进
                indent = ' ' * indent_spaces
                
                # 格式化列表标记
                if marker.isalpha():
                    formatted_marker = f"{marker}."
                else:
                    formatted_marker = f"{marker}."
                
                processed_lines.append(f"{indent}{formatted_marker} {content}")
                
            # 检查是否是无序列表
            elif is_unordered_list(stripped_line):
                content = is_unordered_list(stripped_line).group(1)
                
                # 计算实际缩进
                indent_spaces = self.list_indent * (indent_level + 1)  # 基础缩进加上层级缩进
                indent = ' ' * indent_spaces
                
                processed_lines.append(f"{indent}• {content}")
                
            else:
                # 普通文本行
                processed_lines.append(line)
        
        return '\n'.join(processed_lines)
    
    def get_wrapped_text(self, text, font, max_width):
        """处理文本自动换行，返回带位置信息的行，支持列表缩进"""
        wrapped_info = []
        current_position = 0
        
        # 列表标记的正则表达式
        list_pattern = r'^(\s*)((?:\d+[.、)]|[a-zA-Z][.、)]|[-•*○◆◇])\s+)(.+)$'
        
        print("\n=== 开始处理文本换行 ===")
        print(f"最大宽度: {max_width}")
        
        # 处理文本中的每一行
        paragraphs = text.split('\n')
        print(f"总段落数: {len(paragraphs)}")
        
        for i, paragraph in enumerate(paragraphs):
            print(f"\n处理段落 {i+1}:")
            print(f"原始文本: '{paragraph}'")
            
            if not paragraph:  # 空行处理
                print("空行处理")
                wrapped_info.append({
                    'text': '',
                    'start': current_position,
                    'end': current_position + 1
                })
                current_position += 1
                continue
            
            # 检查是否是列表项
            list_match = re.match(list_pattern, paragraph)
            if list_match:
                print("检测到列表项")
                # 提取列表项的组成部分
                leading_spaces, list_marker, content = list_match.groups()
                indent = leading_spaces + list_marker
                indent_width = font.getlength(indent)
                
                # 记录缩进长度，用于颜色位置的调整
                indent_length = len(indent)
                print(f"缩进字符长度: {indent_length}")
                print(f"缩进宽度: {indent_width}")
                
                # 处理第一行（包含列表标记）
                current_line = paragraph
                line_start = current_position
                current_width = font.getlength(current_line)
                
                # 如果第一行太长，需要分行处理
                if current_width > max_width:
                    # 先添加列表标记和能放下的内容
                    break_point = len(indent)
                    test_width = indent_width
                    
                    # 逐字符尝试添加内容
                    for char in content:
                        char_width = font.getlength(char)
                        if test_width + char_width <= max_width:
                            break_point += 1
                            test_width += char_width
                        else:
                            break
                    
                    # 添加第一行
                    first_line = current_line[:break_point]
                    print(f"第一行文本: '{first_line}'")
                    wrapped_info.append({
                        'text': first_line,
                        'start': line_start,
                        'end': line_start + len(first_line),
                        'is_list_item': True,
                        'indent': indent,
                        'indent_length': indent_length
                    })
                    current_position += len(first_line)
                    
                    # 处理剩余内容
                    remaining_content = current_line[break_point:].lstrip()
                    while remaining_content:
                        # 创建带缩进的新行
                        continuation_indent = ' ' * len(indent)
                        indented_line = continuation_indent + remaining_content
                        print(f"带缩进的新行: '{indented_line}'")
                        
                        # 计算可以放入的文本长度
                        break_point = len(continuation_indent)
                        test_width = font.getlength(continuation_indent)
                        
                        # 逐字符尝试添加内容
                        for char in remaining_content:
                            char_width = font.getlength(char)
                            if test_width + char_width <= max_width:
                                break_point += 1
                                test_width += char_width
                            else:
                                break
                        
                        # 添加换行后的内容
                        wrapped_line = indented_line[:break_point]
                        print(f"换行后内容: '{wrapped_line}'")
                        wrapped_info.append({
                            'text': wrapped_line,
                            'start': current_position,
                            'end': current_position + len(wrapped_line),
                            'is_list_item': True,
                            'indent': continuation_indent,
                            'indent_length': len(continuation_indent)
                        })
                        
                        current_position += len(wrapped_line)
                        remaining_content = indented_line[break_point:].lstrip()
                        print(f"更新后的剩余内容: '{remaining_content}'")
                else:
                    # 如果第一行不需要换行，直接添加
                    print("第一行不需要换行")
                    wrapped_info.append({
                        'text': current_line,
                        'start': line_start,
                        'end': line_start + len(current_line),
                        'is_list_item': True,
                        'indent': indent,
                        'indent_length': indent_length
                    })
                    current_position += len(current_line)
            else:
                print("普通文本处理")
                # 非列表项的普通文本处理
                current_line = ""
                line_start = current_position
                current_width = 0
                
                for char in paragraph:
                    char_width = font.getlength(char)
                    
                    if current_width + char_width > max_width and current_line:
                        # 添加当前行
                        print(f"添加普通行: '{current_line}'")
                        wrapped_info.append({
                            'text': current_line,
                            'start': line_start,
                            'end': line_start + len(current_line)
                        })
                        current_line = ""
                        current_width = 0
                        line_start = current_position
                    
                    current_line += char
                    current_width += char_width
                    current_position += 1
                
                # 添加最后一行
                if current_line:
                    print(f"添加最后一行: '{current_line}'")
                    wrapped_info.append({
                        'text': current_line,
                        'start': line_start,
                        'end': current_position
                    })
        
        # 处理段落结束
        if i < len(paragraphs) - 1:
            current_position += 1
        
        print("\n处理结果:")
        for i, line in enumerate(wrapped_info):
            print(f"行 {i+1}: '{line['text']}'")
            if line.get('is_list_item'):
                print(f"  缩进: '{line['indent']}'")
        
        return wrapped_info
    
    def render_text(self, draw, text_content, font):
        """渲染文本到图片，支持颜色和列表缩进"""
        current_y = self.margin
        
        print("\n=== 开始渲染文本 ===")
        
        for item in text_content:
            if not item.get('text'):
                continue
            
            # 获取文本和颜色信息
            colors = item.get('colors', [])
            font_size = item.get('font_size', 48 if item['type'] == 'title' else 32)
            line_spacing = item.get('line_spacing', 45)
            
            print(f"\n渲染文本块:")
            print(f"类型: {item['type']}")
            print(f"字体大小: {font_size}")
            print(f"行间距: {line_spacing}")
            print(f"颜色信息: {colors}")
            
            try:
                current_font = ImageFont.truetype(font.path, font_size)
                print(f"成功加载字体，大小: {font_size}")
            except Exception as e:
                print(f"字体加载失败: {str(e)}")
                continue
            
            # 获取换行后的文本
            wrapped_lines = item.get('wrapped_lines', [])
            print(f"总行数: {len(wrapped_lines)}")
            
            # 渲染每一行
            for line_info in wrapped_lines:
                if not line_info['text'].strip():
                    current_y += line_spacing // 2
                    continue
                
                print(f"\n渲染行: '{line_info['text']}'")
                print(f"行位置: {line_info['start']}-{line_info['end']}")
                
                # 计算行的起始位置
                if item['type'] == 'title':
                    text_width = sum(current_font.getlength(char) for char in line_info['text'])
                    x = (self.width - text_width) // 2
                    print(f"标题行，居中位置: {x}")
                else:
                    x = self.margin
                    indent_length = 0
                    if line_info.get('is_list_item'):
                        indent = line_info.get('indent', '')
                        indent_length = line_info.get('indent_length', 0)
                        x += current_font.getlength(indent)
                        print(f"列表项，缩进长度: {indent_length}, 缩进后位置: {x}")
                    else:
                        print(f"普通行，左对齐位置: {x}")
                
                current_x = x
                
                # 逐字符渲染，应用颜色
                text_start = line_info['start']
                for i, char in enumerate(line_info['text']):
                    char_position = text_start + i
                    if line_info.get('is_list_item'):
                        # 对列表项，需要考虑缩进的影响
                        actual_position = char_position - indent_length
                        print(f"字符 '{char}' 原始位置: {char_position}, 调整后位置: {actual_position}")
                        char_color = 'black'
                        
                        # 使用调整后的位置查找颜色
                        for color_info in colors:
                            if color_info['start'] <= actual_position < color_info['end']:
                                char_color = color_info['color']
                                print(f"字符 '{char}' 使用颜色: {char_color}")
                                break
                    else:
                        # 非列表项正常处理
                        char_color = 'black'
                        for color_info in colors:
                            if color_info['start'] <= char_position < color_info['end']:
                                char_color = color_info['color']
                                print(f"字符 '{char}' 使用颜色: {char_color}")
                                break
                    
                    draw.text((current_x, current_y), char, font=current_font, fill=char_color)
                    current_x += current_font.getlength(char)
                
                current_y += line_spacing
                print(f"行渲染完成，Y坐标更新到: {current_y}")
        
        print("\n=== 文本渲染完成 ===")
    
    def draw_styled_text(self, draw, text, marks, x, y, font, char_spacing=0, line_spacing=20):
        """绘制带样式的文本"""
        char_width = font.getlength("测")  # 使用一个汉字宽度作为参考
        space_width = font.getlength(" ")  # 获取空格的宽度
        line_height = font.size + line_spacing / 4  # 行高等于字体大小加行间距
        
        # 计算每行最大宽度（考虑右边距）
        max_width = self.width - (self.margin * 2)
        
        # 分行处理文本
        lines = []
        current_line = []
        current_width = 0
        
        # 从左边距开始
        x = self.margin
        
        # 分行处理文本
        for i, char in enumerate(text):
            if char == '\n':  # 处理符
                if current_line:
                    lines.append((current_line, current_width))
                    current_line = []
                    current_width = 0
                continue
            
            # 计算字符宽度（包空格）
            char_full_width = font.getlength(char) + char_spacing
            
            # 检查是否需要换行
            if current_width + char_full_width > max_width and current_line:
                # 当前行已满，开始新行
                lines.append((current_line, current_width))
                current_line = []
                current_width = 0
            
            # 添加字符到当前行
            current_line.append((i, char))
            current_width += char_full_width
        
        # 添加最后一行
        if current_line:
            lines.append((current_line, current_width))
        
        # 计算总高度，确保文本垂直居中
        total_height = len(lines) * line_height
        start_y = (self.height - total_height) // 2
        
        # 先绘制椭圆（确保在文字下面）
        for (start, end), style in marks.items():
            if style['type'] == 'ellipse':
                # 找到起始和结束字符的位置
                start_line = -1
                end_line = -1
                start_x = 0
                end_x = 0
                
                for line_idx, (line_chars, _) in enumerate(lines):
                    for char_idx, (text_idx, _) in enumerate(line_chars):
                        if text_idx == start:
                            start_line = line_idx
                            start_x = x + char_idx * (char_width + char_spacing)
                        if text_idx == end:
                            end_line = line_idx
                            end_x = x + (char_idx + 1) * (char_width + char_spacing)
                
                if start_line == end_line:  # 同一行
                    ellipse_y = start_y + start_line * line_height
                    draw.ellipse([
                        start_x - style.get('size', 10),
                        ellipse_y - style.get('size', 10) + style.get('position', 0),
                        end_x + style.get('size', 10),
                        ellipse_y + font.size + style.get('size', 10) + style.get('position', 0)
                    ], outline=style.get('color', '#000000'), width=style.get('width', 2))
        
        # 绘制文字和其他样式
        for line_idx, (line_chars, line_width) in enumerate(lines):
            current_y = start_y + line_idx * line_height
            current_x = x  # 重置到边距
            
            # 收集每行的下划线信息
            underlines = []
            current_underline = None
            
            for char_idx, (text_idx, char) in enumerate(line_chars):
                # 计算每个字符的实际宽度
                actual_width = font.getlength(char)
                
                # 检查下划线样式
                for (start, end), style in marks.items():
                    if style['type'] == 'underline' and start <= text_idx <= end:
                        if current_underline is None:
                            current_underline = {
                                'start_x': current_x,
                                'color': style.get('color', '#000000'),
                                'width': style.get('width', 2),
                                'offset': style.get('offset', 5)
                            }
                        current_underline['end_x'] = current_x + actual_width
                        break
                else:
                    if current_underline is not None:
                        underlines.append(current_underline)
                        current_underline = None
                
                # 绘制文字（包括空格）
                draw.text((current_x, current_y), char, font=font, fill='black')
                
                # 更新 x 坐标，考虑字间距
                current_x += actual_width + char_spacing
            
            # 添加最后一个下划线
            if current_underline is not None:
                underlines.append(current_underline)
            
            # 绘制该行的所有下划线
            for underline in underlines:
                line_y = current_y + font.size + underline['offset']
                draw.line(
                    [(underline['start_x'], line_y), 
                     (underline['end_x'], line_y)],
                    fill=underline['color'],
                    width=underline['width']
                )
    
    def create_font(self, size, is_bold=False):
        """
        创建字体对象
        
        参数:
            size (int): 字体大小
            is_bold (bool): 是否使用粗体，默认False
            
        返回:
            PIL.ImageFont: 字体对象
            
        功能:
            - 支持普和粗体字体
            - 自动降级到系统字体
            - 处理字体加载失败的情况
            - 提供详细的日志信息
        """
        try:
            # 根据是否加粗选择不同的字体文件
            if is_bold:
                font_name = 'SourceHanSansHWSC-Bold.otf'
            else:
                font_name = 'SourceHanSansCN-VF.ttf'
            
            print(f"\n=== 创建字体 ===")
            print(f"字体大小: {size}")
            print(f"是加: {is_bold}")
            print(f"选择字体文件: {font_name}")
            
            # 获取字体路
            if hasattr(sys, '_MEIPASS'):
                font_path = os.path.join(sys._MEIPASS, 'resources', 'fonts', font_name)
            else:
                font_path = os.path.join('resources', 'fonts', font_name)
            
            print(f"字体完整路径: {font_path}")
            print(f"字体文件是否存在: {os.path.exists(font_path)}")

            # 创建字体对
            font = ImageFont.truetype(font_path, size)
            print("字体创建成功")
            return font
        
        except Exception as e:
            print(f"创建字体失败: {str(e)}")
            print(f"错误类型: {type(e)}")
            # 如果创建失败，尝试使用系统默认字体
            try:
                print("尝试使用系统默认字体 arial.ttf")
                return ImageFont.truetype("arial.ttf", size)
            except Exception as e2:
                print(f"加载系统默认字体也败: {str(e2)}")
                print("使 PIL 默认字体")
                return ImageFont.load_default()
    
    def calculate_block_height(self, wrapped_lines, item):
        """
        计算内容���的总高度
        
        参数:
            wrapped_lines (list): 含行信息的典列表
            item (dict): 内容块信息，包含类型和间距设置
            
        返回:
            int: 内容块的总高度（像素）
        """
        if not wrapped_lines:
            return 0
        
        total_height = 0
        line_spacing = item.get('line_spacing', 45)
        
        for line_info in wrapped_lines:
            if not line_info['text'].strip():  # 空白行
                # 空白行使用半个行间距
                total_height += line_spacing // 2
            else:
                # 正常行使用完整行间距
                total_height += line_spacing
            
            # 如果是标题块且有下一个内容块，添加额外的间距
            if item['type'] == 'title' and line_info == wrapped_lines[-1]:
                total_height += line_spacing // 2
        
        self.logger.debug(f"内容块高度计算: {len(wrapped_lines)} 行, 总高度 {total_height}")
        return total_height
    
    def adjust_color_info(self, colors, start_offset, end_offset):
        """调整颜色信息的位置"""
        adjusted_colors = []
        for color_info in colors:
            if color_info['start'] < end_offset and color_info['end'] > start_offset:
                new_color = dict(color_info)
                new_color['start'] = max(0, color_info['start'] - start_offset)
                new_color['end'] = min(end_offset - start_offset, color_info['end'] - start_offset)
                if new_color['end'] > new_color['start']:
                    adjusted_colors.append(new_color)
        return adjusted_colors