from PIL import Image, ImageDraw, ImageFont
import os
import textwrap
import re
import sys
import logging
from datetime import datetime

class ImageGenerator:
    def __init__(self):
        self.width = 1080
        self.height = 1440  # 3:4 比例
        self.margin = 50  # 边距
        self.list_indent = 30  # 列表缩进
        
        # 设置日志
        self.setup_logger()
        self.fonts = self.load_fonts()
        
    def setup_logger(self):
        """配置日志"""
        # 创建logs目录
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # 生成日志文件名，包含时间戳
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join('logs', f'image_generator_{timestamp}.log')
        
        # 配置日志格式
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger('ImageGenerator')
        self.logger.info('ImageGenerator initialized')
        
    def load_fonts(self):
        """加载字体"""
        fonts = {}
        try:
            # 获取资源路径
            if hasattr(sys, '_MEIPASS'):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.abspath('.')
            
            fonts_dir = os.path.join(base_path, 'resources', 'fonts')
            font_path = os.path.join(fonts_dir, 'MSYH.TTF')
            
            if not os.path.exists(font_path):
                self.logger.error(f"Font file not found at: {font_path}")
                raise FileNotFoundError(f"Font file not found: {font_path}")
                
            fonts['normal'] = ImageFont.truetype(font_path, 32)
            self.logger.info("Fonts loaded successfully")
            return fonts
        except Exception as e:
            self.logger.error(f"Error loading fonts: {str(e)}")
            return {}
        
    def create_images(self, text_content, background_path, font_style='normal'):
        """生成多页图片"""
        try:
            images = []
            remaining_content = text_content.copy()
            
            while remaining_content:
                # 创建新页面
                image = Image.new('RGB', (self.width, self.height), 'white')
                if background_path:
                    try:
                        bg = Image.open(background_path)
                        bg = bg.resize((self.width, self.height))
                        image.paste(bg, (0, 0))
                        self.logger.debug("背景加载成功")
                    except Exception as e:
                        self.logger.error(f"背景加载失败: {str(e)}")
                
                draw = ImageDraw.Draw(image)
                current_page_content = []
                current_y = self.margin
                
                # 处理当前页面的内容
                while remaining_content:
                    item = remaining_content[0]
                    font_size = item.get('font_size', 48 if item['type'] == 'title' else 32)
                    
                    try:
                        current_font = ImageFont.truetype(self.fonts[font_style].path, font_size)
                    except Exception as e:
                        self.logger.error(f"字体加载失败: {str(e)}")
                        remaining_content.pop(0)
                        continue
                    
                    # 如果内容已经预处理过，直接使用
                    if 'wrapped_lines' in item:
                        wrapped_lines = item['wrapped_lines']
                    else:
                        # 预处理文本换行
                        max_width = self.width - (self.margin * 2)
                        wrapped_lines = self.get_wrapped_text(item['text'], current_font, max_width)
                    
                    # 计算此内容块的高度
                    block_height = self.calculate_block_height(wrapped_lines, item)
                    
                    # 检查是否需要新页面
                    if current_y + block_height > self.height - self.margin:
                        if not current_page_content:
                            # 如果是第一个内容块且太大，需要强制分割
                            self.logger.warning(f"内容块太大，需要分割: {block_height} > {self.height - current_y - self.margin}")
                            
                            # 计算当前页面可以容纳的行数
                            available_height = self.height - current_y - self.margin
                            line_spacing = item.get('line_spacing', 45)
                            max_lines = int(available_height / line_spacing)
                            
                            if max_lines > 0:
                                # 分割内容
                                current_lines = wrapped_lines[:max_lines]
                                remaining_lines = wrapped_lines[max_lines:]
                                
                                # 创建分割后的内容块
                                current_item = dict(item)
                                current_item['wrapped_lines'] = current_lines
                                
                                remaining_item = dict(item)
                                remaining_item['wrapped_lines'] = remaining_lines
                                
                                current_page_content.append(current_item)
                                remaining_content[0] = remaining_item
                                self.logger.debug(f"内容块分割完成: 当前页 {len(current_lines)} 行，剩余 {len(remaining_lines)} 行")
                            else:
                                self.logger.error("页面空间不足，跳过当前内容块")
                                remaining_content.pop(0)
                        break
                    
                    # 将预处理后的内容添加到当前页面
                    processed_item = dict(item)
                    processed_item['wrapped_lines'] = wrapped_lines
                    current_page_content.append(processed_item)
                    current_y += block_height
                    
                    # 从剩余内容中移除已处理的项
                    remaining_content.pop(0)
                
                # 渲染当前页面的内容
                if current_page_content:
                    self.render_text(draw, current_page_content, self.fonts[font_style])
                    images.append(image)
                    self.logger.info(f"完成第 {len(images)} 页")
                else:
                    self.logger.warning("当前页面没有内容可渲染")
                    if remaining_content:
                        remaining_content.pop(0)
                
                # 添加Logo
                try:
                    self.add_logo_to_images([image])
                    self.logger.info("Logo添加成功")
                except Exception as e:
                    self.logger.error(f"Logo添加失败: {str(e)}")
            
            return images
            
        except Exception as e:
            self.logger.error(f"生成图片错误: {str(e)}")
            raise
    
    def calculate_content_height(self, content_items, font):
        """计算内容块的总高度"""
        total_height = 0
        for item in content_items:
            if not item.get('text', '').strip():
                continue
                
            # 使用内容块自带的字体大小
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
        """将文本按行数分割"""
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
        print(f"文本内容: {text_content.get('text', '')[:50]}...")  # 只印前50个字符
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
        print("\n3333333333333333333333333")
        print(text)
        print("\n3333333333333333333333333")
        font_size = text_content.get('font_size', 48)
        line_spacing = text_content.get('line_spacing', 20)
        char_spacing = text_content.get('char_spacing', 0)
        marks = text_content.get('marks', {})
        is_bold = text_content.get('font_bold', False)  # 获取加粗设置
        
        print("\n=== 文本渲染参数 ===")
        print(f"行间距: {line_spacing}")
        print(f"字间距: {char_spacing}")
        print(f"样式标记数: {len(marks)}")
        
        # 创建字体对象，传入加粗参数
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
                    # 将原图转换为 RGBA 模式
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
        list_stack = []  # 用于跟踪套列表
        
        # 扩展列表标记正则表达式
        ordered_patterns = [
            r'(\d+)[.、)]\s+(.+)',  # 数字列表：1. 1、 1)
            r'([a-z])[.、)]\s+(.+)',  # 字母列表：a. a、 a)
            r'([A-Z])[.、)]\s+(.+)'  # 大写字母列表：A. A、 A)
        ]
        unordered_patterns = [
            r'[-•*]\s+(.+)',        # 常规无序列表标记
            r'[○◆◇]\s+(.+)'      # 其他无列表标记
        ]
        
        def get_indent_level(line):
            """获取缩进级别"""
            return len(line) - len(line.lstrip())
        
        def is_ordered_list(line):
            """检查是否是有序列表项"""
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
        # 用于跟踪每个缩进级别的起始值
        list_start_numbers = {}
        
        for line in lines:
            if not line.strip():
                processed_lines.append('')
                continue
                
            indent_level = get_indent_level(line)
            stripped_line = line.lstrip()
            
            # 根据缩进调整列表堆栈
            while list_stack and list_stack[-1]['indent'] >= indent_level:
                popped = list_stack.pop()
                # 当退出一个缩进级别时，清除该级别的编号记录
                if popped['indent'] in current_list_number:
                    del current_list_number[popped['indent']]
            
            # 检查是否是有序列表
            ordered_match = is_ordered_list(stripped_line)
            if ordered_match:
                marker, content = ordered_match.groups()
                
                # 如果是新的缩进级别或新的列表开始
                if indent_level not in current_list_number:
                    # 保存起始编号
                    if marker.isalpha():
                        start_num = ord(marker.lower()) - ord('a') + 1
                    else:
                        start_num = int(marker)
                    current_list_number[indent_level] = start_num
                    list_start_numbers[indent_level] = start_num
                else:
                    # 使用已存在的编号
                    current_list_number[indent_level] += 1
                
                list_stack.append({
                    'type': 'ordered',
                    'indent': indent_level,
                    'counter': current_list_number[indent_level],
                    'marker_type': 'alpha' if marker.isalpha() else 'numeric'
                })
                
                # 生成适当的标记
                if list_stack[-1]['marker_type'] == 'alpha':
                    marker = chr(ord('a') + current_list_number[indent_level] - 1)
                    formatted_marker = f"{marker}."
                else:
                    formatted_marker = f"{current_list_number[indent_level]}."
                
                indent = ' ' * indent_level
                processed_lines.append(f"{indent}{formatted_marker} {content}")
                
            # 检查是否是无序列表
            elif is_unordered_list(stripped_line):
                content = is_unordered_list(stripped_line).group(1)
                
                list_stack.append({
                    'type': 'unordered',
                    'indent': indent_level
                })
                
                indent = ' ' * indent_level
                processed_lines.append(f"{indent}• {content}")
                
            else:
                # 普通文本行
                processed_lines.append(line)
                if not line.strip():
                    list_stack = []
                    current_list_number = {}
                    list_start_numbers = {}
            
        return '\n'.join(processed_lines)
    
    def get_wrapped_text(self, text, font, max_width):
        """将文本按照最大宽度换行，支持列表格式和前导空格"""
        def get_next_break_point(text, start_idx, current_width, max_width):
            """找下一个合适的换行点"""
            width = current_width
            i = start_idx
            
            # 计算前导空格的宽度
            while i < len(text) and text[i].isspace():
                width += font.getlength(text[i])
                i += 1
            
            while i < len(text):
                char = text[i]
                char_width = font.getlength(char)
                
                if width + char_width > max_width:
                    # 如果是第一个字符就超出宽度，至少返回这个字符的位置
                    return i if i > start_idx else i + 1
                
                width += char_width
                i += 1
            
            return i

        # 检查是否是列表项，扩展匹配模式以支持多种列表标记
        list_match = re.match(r'^(\s*)((?:\d+[.、)]|[a-z][.、)]|[-•*])\s+)(.+)$', text)
        lines = []
        
        if list_match:
            # 列表项处理
            indent = list_match.group(1)  # 缩进
            marker = list_match.group(2)  # 列表标记
            content = list_match.group(3)  # 实际内容
            
            # 计算列表标记的实际宽度
            marker_width = sum(font.getlength(c) for c in marker)
            
            # 计算后续行的缩进宽度（缩进 + 标记的宽度）
            indent_width = sum(font.getlength(' ') for _ in range(len(indent)))
            total_indent_width = indent_width + marker_width
            
            # 计算可用宽度
            available_width = max_width - total_indent_width
            
            # 处理内容部分
            paragraphs = content.split('\n')
            first_line = True
            
            for paragraph in paragraphs:
                # 检查段落是否是新的列表项
                sub_list_match = re.match(r'^(\s*)((?:\d+[.、)]|[a-z][.、)]|[-���*])\s+)(.+)$', paragraph)
                if sub_list_match and not first_line:
                    # 果是新的列表项，递归处理
                    sub_lines = self.get_wrapped_text(paragraph, font, max_width)
                    lines.extend(sub_lines)
                    continue
                    
                # 处理段落
                start_idx = 0
                while start_idx < len(paragraph):
                    # 获取下一个换行点
                    break_point = get_next_break_point(
                        paragraph, 
                        start_idx, 
                        0,
                        available_width
                    )
                    
                    # 添加行，保留前导空格
                    line = paragraph[start_idx:break_point]
                    if line:
                        if first_line:
                            # 第一行使用原始缩进和标记
                            lines.append(indent + marker + line)
                            first_line = False
                        else:
                            # 后续行使用相同宽度的空格缩进
                            # 计算需要多少个空格来达到相同的缩进宽度
                            space_width = font.getlength(' ')
                            indent_spaces = ' ' * (int(total_indent_width / space_width) + 1)
                            lines.append(indent_spaces + line)
                    
                    # 更新开始位置
                    start_idx = break_point
                
                # 在段落之间添加空行标记
                if paragraph != paragraphs[-1]:
                    lines.append('\n')
        else:
            # 处理普通段落
            paragraphs = text.split('\n')
            
            for i, paragraph in enumerate(paragraphs):
                # 检查是否是列表项
                list_match = re.match(r'^(\s*)((?:\d+[.、)]|[a-z][.、)]|[-•*])\s+)(.+)$', paragraph)
                if list_match:
                    # 如果是列表项，递归处理
                    sub_lines = self.get_wrapped_text(paragraph, font, max_width)
                    lines.extend(sub_lines)
                    continue
                    
                # 处理空行
                if not paragraph.strip():
                    if i > 0 and paragraphs[i-1].strip():
                        lines.append('\n')
                    continue
                
                # 处理非空段落
                start_idx = 0
                while start_idx < len(paragraph):
                    # 获取下一个换行点，保留前导空格
                    break_point = get_next_break_point(
                        paragraph,
                        start_idx,
                        0,
                        max_width
                    )
                    
                    # 添加行，保留所有空格
                    line = paragraph[start_idx:break_point]
                    if line or line.isspace():  # 保留纯空格的行
                        lines.append(line)
                    
                    # 更新开始位置
                    start_idx = break_point
                
                # 在非空段落之间添加换行标记
                if i < len(paragraphs) - 1 and paragraphs[i+1].strip():
                    lines.append('\n')

        self.logger.debug("处理后的行:")
        for i, line in enumerate(lines):
            self.logger.debug(f"第 {i+1} 行: '{line}'")
        
        return lines
    
    def render_text(self, draw, text_content, font):
        """渲染文字到图片"""
        current_y = self.margin
        last_item_type = None
        
        for item in text_content:
            if not item.get('text'):
                continue
            
            # 使用预处理的换行结果
            lines = item['wrapped_lines']
            font_size = item.get('font_size', 48 if item['type'] == 'title' else 32)
            line_spacing = item.get('line_spacing', 45)
            
            try:
                current_font = ImageFont.truetype(font.path, font_size)
            except Exception as e:
                self.logger.error(f"字体加载失败: {str(e)}")
                continue
            
            # 处理标题和内容块之间的间距
            if last_item_type == 'title' and item['type'] == 'content':
                current_y += line_spacing // 2
            
            # 渲染每一行
            for line in lines:
                if not line.strip():  # 空白行
                    current_y += line_spacing // 2
                    continue
                
                # 计算行的位置
                if item['type'] == 'title':
                    text_width = sum(current_font.getlength(char) for char in line)
                    x = (self.width - text_width) // 2
                else:
                    x = self.margin
                
                # 渲染文本
                draw.text((x, current_y), line, font=current_font, fill='black')
                current_y += line_spacing
            
            last_item_type = item['type']
    
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
            if char == '\n':  # 处理换行符
                if current_line:
                    lines.append((current_line, current_width))
                    current_line = []
                    current_width = 0
                continue
            
            # 计算字符宽度（包括空格）
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
            current_x = x  # 重置到左边距
            
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
        """创建体对象，支持不同字重的字体"""
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
            
            # 获取字体路径
            if hasattr(sys, '_MEIPASS'):
                font_path = os.path.join(sys._MEIPASS, 'resources', 'fonts', font_name)
            else:
                font_path = os.path.join('resources', 'fonts', font_name)
            
            print(f"字体完整路径: {font_path}")
            print(f"字体文件是否存在: {os.path.exists(font_path)}")

            # 创建字体对象
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
    
    def add_logo_to_images(self, images):
        """为所有图片添加Logo"""
        try:
            # 获取 logo 路径
            if hasattr(sys, '_MEIPASS'):
                logo_path = os.path.join(sys._MEIPASS, 'resources', 'icons', 'logo.png')
            else:
                logo_path = os.path.join('resources', 'icons', 'logo.png')
            
            print(f"\n=== 添加 Logo ===")
            print(f"Logo 路径: {logo_path}")
            print(f"Logo 文件是否存在: {os.path.exists(logo_path)}")
            
            if os.path.exists(logo_path):
                # 加载 logo
                logo = Image.open(logo_path)
                print(f"Logo 模式: {logo.mode}")
                print(f"Logo 寸: {logo.size}")
                
                # 设置 logo 大小
                logo_height = 60  # logo 的目标高度
                aspect_ratio = logo.width / logo.height
                logo_width = int(logo_height * aspect_ratio)
                
                # 调整 logo 大小
                logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
                print(f"调整后的 Logo 尺寸: {logo.size}")
                
                # 计算 logo 位置（左下角，留出边距）
                margin = 20  # 边距
                x = margin
                y = self.height - logo_height - margin
                print(f"Logo 位置: ({x}, {y})")
                
                # 为每个图片添加 logo
                for i, image in enumerate(images):
                    if logo.mode == 'RGBA':
                        print("处理带透明通道的 Logo")
                        # 将原图转换为 RGBA 模式
                        image = image.convert('RGBA')
                        # 创建一个与原图大小相同的透明图层
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
                    
                    # 更新图片列表
                    images[i] = image
                
                print("Logo 添加成功")
            else:
                print(f"Logo 文件不存在: {logo_path}")
                
        except Exception as e:
            print(f"添加 Logo 失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def calculate_block_height(self, wrapped_lines, item):
        """计算内容块的总高度，包括行间距和空白行"""
        if not wrapped_lines:
            return 0
        
        total_height = 0
        line_spacing = item.get('line_spacing', 45)
        
        for i, line in enumerate(wrapped_lines):
            if not line.strip():  # 空白行
                # 空白行使用半个行间距
                total_height += line_spacing // 2
            else:
                # 正常行使用完整行间距
                total_height += line_spacing
            
            # 如果是标题块且有下一个内容块，添加额外的间距
            if item['type'] == 'title' and i == len(wrapped_lines) - 1:
                total_height += line_spacing // 2
        
        self.logger.debug(f"内容块高度计算: {len(wrapped_lines)} 行, 总高度 {total_height}")
        return total_height