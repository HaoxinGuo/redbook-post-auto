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
        """生成多页图片，优化空白行处理"""
        images = []
        remaining_content = text_content.copy()
        
        self.logger.info("=== 开始生成图片 ===")
        self.logger.info(f"总内容块数: {len(text_content)}")
        
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
            
            while remaining_content and current_y < self.height - self.margin:
                # 获取下一个内容块
                item = remaining_content[0]
                if not item.get('text', '').strip():
                    remaining_content.pop(0)
                    continue
                
                # 设置字体
                font_size = item.get('font_size', 48 if item['type'] == 'title' else 32)
                line_spacing = item.get('line_spacing', 45)
                
                try:
                    current_font = ImageFont.truetype(self.fonts[font_style].path, font_size)
                except Exception as e:
                    self.logger.error(f"字体加载失败: {str(e)}")
                    remaining_content.pop(0)
                    continue
                
                # 计算可用高度
                available_height = self.height - current_y - self.margin
                
                # 获取文本的实际换行
                text = item['text']
                max_width = self.width - (self.margin * 2)
                wrapped_lines = self.get_wrapped_text(text, current_font, max_width)
                
                # 计算这些行实际需要的高度
                total_height = 0
                used_lines = []
                
                for line in wrapped_lines:
                    line_height = line_spacing
                    if total_height + line_height <= available_height:
                        used_lines.append(line)
                        total_height += line_height
                    else:
                        break
                
                # 如果当前页面能放下一些内容
                if used_lines:
                    partial_content = {
                        'type': item['type'],
                        'text': '\n'.join(used_lines),
                        'line_spacing': line_spacing,
                        'font_size': font_size
                    }
                    current_page_content.append(partial_content)
                    
                    # 更新剩余内容
                    unused_lines = wrapped_lines[len(used_lines):]
                    if unused_lines:
                        remaining_content[0] = {
                            'type': item['type'],
                            'text': '\n'.join(unused_lines),
                            'line_spacing': line_spacing,
                            'font_size': font_size
                        }
                    else:
                        remaining_content.pop(0)
                    
                    current_y += total_height
                else:
                    # 如果一行都放不下，创建新页面
                    break
            
            # 渲染当前页面的内容
            if current_page_content:
                self.render_text(draw, current_page_content, self.fonts[font_style])
                images.append(image)
                self.logger.info(f"完成第 {len(images)} 页")
        
        # 添加Logo
        try:
            self.add_logo_to_images(images)
            self.logger.info("Logo添加成功")
        except Exception as e:
            self.logger.error(f"Logo添加失败: {str(e)}")
        
        self.logger.info(f"=== 图片生成完成，共 {len(images)} 页 ===")
        return images
    
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
        print(f"字体对象创建结果: {font}")
        
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
                
                # 计算 logo 位置（左下角，留出边��）
                margin = 40  # 边距
                x = margin
                y = self.height - logo_height - margin
                print(f"Logo 位置: ({x}, {y})")
                
                # 如果 logo 有透明通，需要特殊处理
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
            r'[○◆◇]\s+(.+)'      # 其他无序列表标记
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
        """将文本按照最大宽度换行，支持列表格式"""
        def get_next_break_point(text, start_idx, current_width, max_width):
            """找下一个合适的换行点"""
            width = current_width
            i = start_idx
            
            while i < len(text):
                char = text[i]
                char_width = font.getlength(char)
                
                # 如果加上这个字符会超过最大宽度，就在当前位置换行
                if width + char_width > max_width:
                    return i if i > start_idx else i + 1
                
                width += char_width
                i += 1
            
            return i

        # 检查是否是列表项
        list_match = re.match(r'^(\s*)((\d+[.、)]|[a-z][.、)]|\s*[-•*])\s+)(.+)$', text)
        lines = []
        
        if list_match:
            # 列表项处理
            indent = list_match.group(1)  # 缩进
            marker = list_match.group(2)  # 列表标记
            content = list_match.group(4)  # 实际内容
            
            # 计算列表标记的实际宽度
            marker_width = sum(font.getlength(c) for c in marker)
            available_width = max_width - marker_width
            
            # 处理内容部分
            paragraphs = content.split('\n')
            first_line = True
            
            for paragraph in paragraphs:
                if not paragraph.strip():
                    continue
                
                # 处理段落
                start_idx = 0
                while start_idx < len(paragraph):
                    # 获取下一个换行点
                    break_point = get_next_break_point(
                        paragraph, 
                        start_idx, 
                        0, 
                        available_width if first_line else max_width - len(marker) * font.getlength(' ')
                    )
                    
                    # 添加行
                    line = paragraph[start_idx:break_point]
                    if line:
                        prefix = marker if first_line else ' ' * len(marker)
                        lines.append(prefix + line)
                        first_line = False
                    
                    # 更新开始位置
                    start_idx = break_point
        else:
            # 处理普通段落
            paragraphs = text.split('\n')
            
            for paragraph in paragraphs:
                if not paragraph.strip():
                    continue
                
                # 处理段落
                start_idx = 0
                while start_idx < len(paragraph):
                    # 获取下一个换行点
                    break_point = get_next_break_point(
                        paragraph,
                        start_idx,
                        0,
                        max_width
                    )
                    
                    # 添加行
                    line = paragraph[start_idx:break_point]
                    if line:
                        lines.append(line)
                    
                    # 更新开始位置
                    start_idx = break_point
    
        self.logger.debug("处理后的行:")
        for i, line in enumerate(lines):
            self.logger.debug(f"第 {i+1} 行: '{line}'")
        
        return lines
    
    def render_text(self, draw, text_content, font):
        """渲染文字到图片"""
        current_y = self.margin
        last_item_type = None  # 记录上一个内容块的类型
        
        for item in text_content:
            if not item.get('text', '').strip():
                continue
            
            font_size = item.get('font_size', 48 if item['type'] == 'title' else 32)
            line_spacing = item.get('line_spacing', 45)
            alignment = 'center' if item['type'] == 'title' else 'left'
            
            # 如果当前是内容块且上一个内容块是标题，添加半个行间距
            if last_item_type == 'title' and item['type'] != 'title':
                current_y += line_spacing // 2
            
            try:
                current_font = ImageFont.truetype(font.path, font_size)
            except Exception as e:
                print(f"字体加载失败: {str(e)}")
                continue
            
            # 每次渲染时重新计算换行
            max_width = self.width - (self.margin * 2)
            text = item['text']  # 不再使用 strip()，保留原始空格
            lines = self.get_wrapped_text(text, current_font, max_width)
            
            for line in lines:
                if current_y + line_spacing > self.height - self.margin:
                    return False
                
                # 忽略完全空的行，但保留只有空格的行
                if not line:
                    continue
                
                # 计算每行的实际宽度（包括前导空格）
                text_width = sum(current_font.getlength(char) for char in line)
                
                # 计算文本位置
                if alignment == 'center':
                    x = (self.width - text_width) // 2
                else:
                    x = self.margin
                
                try:
                    # 不再使用 strip()，保留原始空格
                    draw.text((x, current_y), line, font=current_font, fill='black')
                    current_y += line_spacing
                except Exception as e:
                    print(f"渲染文字失败: {str(e)}")
            
            # 更新上一个内容块的类型
            last_item_type = item['type']
        
        return True
    
    def draw_styled_text(self, draw, text, marks, x, y, font, char_spacing=0, line_spacing=20):
        """绘制带样式的文本"""
        char_width = font.getlength("测")  # 使用一个汉字宽度作为参考
        line_height = font.size + line_spacing / 3  # 行高等于字体大小加行间距
        
        # 计算每行最大宽度（考虑右边距）
        max_width = self.width - (self.margin * 2)
        
        # 分行处理文本
        lines = []
        current_line = []
        current_width = 0
        
        # 从左边距开始
        x = self.margin
        
        for i, char in enumerate(text):
            if char.strip():
                char_full_width = char_width + char_spacing
                # 检查是否需要换行
                if current_width + char_full_width > max_width:
                    # 当前行已满，开始新行
                    if current_line:  # 确保当前行有内容
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
            
            # 收集每行的下划线息
            underlines = []
            current_underline = None
            
            for char_idx, (text_idx, char) in enumerate(line_chars):
                current_x = x + char_idx * (char_width + char_spacing)
                
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
                        current_underline['end_x'] = current_x + char_width
                        break
                else:
                    if current_underline is not None:
                        underlines.append(current_underline)
                        current_underline = None
                
                # 绘制文字
                draw.text((current_x, current_y), char, font=font, fill='black')
            
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
            print(f"是否加: {is_bold}")
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
                print("使用 PIL 默认字体")
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
                print(f"Logo 尺寸: {logo.size}")
                
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