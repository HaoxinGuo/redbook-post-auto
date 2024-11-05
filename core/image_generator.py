from PIL import Image, ImageDraw, ImageFont
import os
import textwrap
import re

class ImageGenerator:
    def __init__(self):
        self.width = 1080
        self.height = 1440  # 3:4 比例
        self.fonts = self.load_fonts()
        self.margin = 50  # 边距
        self.list_indent = 30  # 列表缩进
        
    def load_fonts(self):
        fonts = {}
        fonts_dir = os.path.join('resources', 'fonts')
        fonts['normal'] = ImageFont.truetype(os.path.join(fonts_dir, 'MSYH.TTF'), 32)
        fonts['handwritten'] = ImageFont.truetype(os.path.join(fonts_dir, 'handwritten.ttf'), 32)
        return fonts
        
    def create_images(self, text_content, background_path, font_style='normal'):
        """生成多页图片"""
        images = []
        current_y = self.margin
        current_content = []
        remaining_text = None  # 存储未完成的文本内容
        
        i = 0
        while i < len(text_content):
            item = text_content[i]
            
            # 如果有未完成的文本，创建新的内容项
            if remaining_text:
                item = {
                    'type': 'content',  # 继承原内容的类型
                    'text': remaining_text
                }
                remaining_text = None
            
            # 计算当前内容块所需高度
            content_height = self.calculate_content_height(item, self.fonts[font_style])
            
            # 如果是标题且当前页面已经有内容，创建新页面
            if item['type'] == 'title' and current_content and current_y > self.margin:
                images.append(self.create_single_image(current_content, background_path, font_style))
                current_content = []
                current_y = self.margin
            
            # 如果内容会超出页面
            if current_y + content_height > self.height - self.margin:
                if current_content:  # 确保有内容才创建新页面
                    # 计算当前页面剩余空间能容纳多少行
                    remaining_height = self.height - self.margin - current_y
                    lines_per_page = self.calculate_lines_per_height(remaining_height, item['type'])
                    
                    # 分割文本
                    first_part, second_part = self.split_text_by_lines(
                        item['text'], 
                        self.fonts[font_style], 
                        lines_per_page,
                        item['type']
                    )
                    
                    if first_part:  # 如果当前页面还能放下一些内容
                        current_content.append({
                            'type': item['type'],
                            'text': first_part
                        })
                    
                    # 创建当前页面
                    images.append(self.create_single_image(current_content, background_path, font_style))
                    current_content = []
                    current_y = self.margin
                    
                    if second_part:  # 保存剩余内容
                        remaining_text = second_part
                        continue  # 继续处理剩余内容
                else:
                    # 如果当前页面为空，强制开始新页面
                    images.append(self.create_single_image(current_content, background_path, font_style))
                    current_content = []
                    current_y = self.margin
            
            # 正常添加内容
            current_content.append(item)
            current_y += content_height
            
            # 只有在没有剩余文本时才增加索引
            if not remaining_text:
                i += 1
        
        # 处理最后一页
        if current_content:
            images.append(self.create_single_image(current_content, background_path, font_style))
        
        return images
    
    def calculate_lines_per_height(self, height, content_type):
        """计算指定高度可以容纳多少行文本"""
        if content_type == 'title':
            line_spacing = 60
            return int(height / line_spacing)
        else:
            line_spacing = 45
            return int(height / line_spacing)
    
    def split_text_by_lines(self, text, font, max_lines, content_type):
        """将文本按行数分割"""
        max_width = self.width - (self.margin * 2)
        lines = self.get_wrapped_text(text, font, max_width)
        
        if len(lines) <= max_lines:
            return text, None
        
        first_part_lines = lines[:max_lines]
        second_part_lines = lines[max_lines:]
        
        # 重新组合文本
        first_part = '\n'.join(first_part_lines)
        second_part = '\n'.join(second_part_lines)
        
        return first_part, second_part
    
    def create_single_image(self, text_content, background_path, font_style='normal'):
        """创建单个图片"""
        # 创建基础图片
        image = Image.new('RGB', (self.width, self.height), 'white')
        
        # 加载背景
        if background_path:
            try:
                bg = Image.open(background_path)
                bg = bg.resize((self.width, self.height))
                image.paste(bg, (0, 0))
            except Exception as e:
                print(f"加载背景图片失败: {str(e)}")
            
        # 创建绘图对象
        draw = ImageDraw.Draw(image)
        
        # 获取字体
        font = self.fonts[font_style]
        
        # 渲染文字
        self.render_text(draw, text_content, font)
        
        return image
    
    def calculate_content_height(self, item, font):
        """计算容块所需的高度"""
        if not item.get('text', '').strip():
            return 0
            
        # 设置字体大小
        if item['type'] == 'title':
            font_size = 48
            line_spacing = 60
        else:
            font_size = 32
            line_spacing = 45
            
        try:
            if item['type'] == 'title':
                font = ImageFont.truetype(font.path, font_size)
            else:
                font = ImageFont.truetype(font.path, font_size)
        except Exception as e:
            print(f"调整字体大小失败: {str(e)}")
            return 0
            
        # 获取换行后的文本
        max_width = self.width - (self.margin * 2)
        lines = self.get_wrapped_text(item['text'], font, max_width)
        
        # 计算总高度
        total_height = len(lines) * line_spacing
        total_height += line_spacing  # 添加段落间距
        
        return total_height

    def process_list_text(self, text):
        """处理文本中的列表"""
        lines = text.split('\n')
        processed_lines = []
        list_stack = []  # 用于跟踪嵌套列表
        
        # 扩展列表标记的正则表达式
        ordered_patterns = [
            r'(\d+)[.、)]\s+(.+)',  # 数字列表：1. 1、 1)
            r'([a-z])[.、)]\s+(.+)',  # 字母列表：a. a、 a)
            r'([A-Z])[.、)]\s+(.+)'  # 大写字母列表：A. A、 A)
        ]
        unordered_patterns = [
            r'[-•*]\s+(.+)',        # 常规无序列表标记
            r'[○●◆◇]\s+(.+)'      # 其他无序列表标记
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
        
        current_list_number = {}  # 用于跟踪每个缩进级别的编号
        
        for line in lines:
            if not line.strip():
                processed_lines.append('')
                continue
                
            indent_level = get_indent_level(line)
            stripped_line = line.lstrip()
            
            # 根据缩进调整列表堆栈
            while list_stack and list_stack[-1]['indent'] >= indent_level:
                list_stack.pop()
                if list_stack and 'counter' in list_stack[-1]:
                    current_list_number[list_stack[-1]['indent']] = list_stack[-1]['counter']
            
            # 检查是否是有序列表
            ordered_match = is_ordered_list(stripped_line)
            if ordered_match:
                marker, content = ordered_match.groups()
                
                # 确定这个缩进级别的起始编号
                if indent_level not in current_list_number:
                    # 如果是字母，将其转换为数字
                    if marker.isalpha():
                        start_num = ord(marker.lower()) - ord('a') + 1
                    else:
                        start_num = int(marker)
                    current_list_number[indent_level] = start_num
                else:
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
        
        return '\n'.join(processed_lines)
    
    def get_wrapped_text(self, text, font, max_width):
        """将文本按照最大宽度换行，支持列表格式"""
        lines = []
        # 处理列表格式
        processed_text = self.process_list_text(text)
        paragraphs = processed_text.split('\n')
        
        # 计算列表标记的最大宽度
        max_marker_width = 0
        for paragraph in paragraphs:
            if not paragraph.strip():
                continue
            # 检查是否是列表项并获取标记部分
            list_match = re.match(r'^(\s*)((\d+[.、)]|[a-z][.、)]|\s*[-•*])\s+)(.+)$', paragraph)
            if list_match:
                indent = list_match.group(1)
                marker = list_match.group(2)
                marker_width = font.getlength(indent + marker)
                max_marker_width = max(max_marker_width, marker_width)
        
        for paragraph in paragraphs:
            if not paragraph:
                lines.append('')
                continue
            
            # 检查是否是列表项
            list_match = re.match(r'^(\s*)((\d+[.、)]|[a-z][.、)]|\s*[-•*])\s+)(.+)$', paragraph)
            
            if list_match:
                # 分解列表项的各个部分
                indent = list_match.group(1)
                marker = list_match.group(2)
                content = list_match.group(4)
                
                # 计算内容的起始位置（统一缩进）
                content_start = max_marker_width + self.list_indent
                
                # 计算实际可用宽度
                available_width = max_width - content_start
                
                # 处理第一行（包含标记）
                first_line = indent + marker + content
                
                # 确保第一行不会太长
                while font.getlength(first_line) > max_width and len(content) > 1:
                    content = content[:-1]
                    first_line = indent + marker + content
                
                lines.append(first_line)
                
                # 处理剩余内容
                remaining_content = content[len(content):]
                if remaining_content:
                    # 创建后续行的缩进
                    subsequent_indent = ' ' * int(content_start / font.getlength(' '))
                    
                    while remaining_content:
                        # 计算这一行可以容纳多少字符
                        line = subsequent_indent
                        for char in remaining_content:
                            test_line = line + char
                            if font.getlength(test_line) > max_width:
                                break
                            line = test_line
                        
                        lines.append(line)
                        remaining_content = remaining_content[len(line)-len(subsequent_indent):]
            else:
                # 处理非列表项文本
                current_text = paragraph
                while current_text:
                    line = ''
                    for char in current_text:
                        test_line = line + char
                        if font.getlength(test_line) > max_width:
                            break
                        line = test_line
                    
                    lines.append(line)
                    current_text = current_text[len(line):]
        
        return lines
    
    def render_text(self, draw, text_content, font):
        """渲染文字到图片上"""
        current_y = self.margin
        max_width = self.width - (self.margin * 2)
        
        for item in text_content:
            if not item.get('text', '').strip():
                continue
            
            # 设置不同类型文本的字体大小
            if item['type'] == 'title':
                font_size = 48
                line_spacing = 60
            else:
                font_size = 32
                line_spacing = 45
            
            try:
                current_font = ImageFont.truetype(font.path, font_size)
            except Exception as e:
                print(f"调整字体大小失败: {str(e)}")
                continue
            
            # 获取换行后的文本
            lines = self.get_wrapped_text(item['text'], current_font, max_width)
            
            # 渲染每一行
            for line in lines:
                if not line:  # 空行处理
                    current_y += line_spacing // 2
                    continue
                
                # 计算文本位置
                if item['type'] == 'title':
                    # 标题居中
                    text_width = current_font.getlength(line)
                    x = (self.width - text_width) // 2
                else:
                    # 正文左对齐
                    x = self.margin
                
                # 绘制文本
                draw.text((x, current_y), line, font=current_font, fill='black')
                current_y += line_spacing
            
            # 在不同文本块之间添加额外的间距
            current_y += line_spacing
            
            # 检查是否超出图片高度
            if current_y > self.height - self.margin:
                break