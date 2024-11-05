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
        current_type = None   # 存储当前处理的内容类型
        
        print(f"\n开始处理文本内容，总内容块数: {len(text_content)}")
        
        i = 0
        while i < len(text_content):
            item = text_content[i]
            print(f"\n处理第 {i+1} 个内容块:")
            print(f"类型: {item['type']}")
            print(f"内容长度: {len(item.get('text', ''))}")
            
            # 跳过空内容
            if not item.get('text', '').strip():
                print("跳过空内容块")
                i += 1
                continue
            
            # 如果有未完成的文本，创建新的内容项
            if remaining_text:
                print(f"处理剩余文本，长度: {len(remaining_text)}")
                item = {
                    'type': current_type or 'content',  # 使用保存的类型
                    'text': remaining_text.strip()
                }
                print(f"剩余文本类型: {item['type']}")
                remaining_text = None
                if not item['text']:
                    print("剩余文本为空，跳过")
                    i += 1
                    continue
            else:
                # 保存当前内容的类型
                current_type = item['type']
            
            # 计算当前内容块所需高度
            content_height = self.calculate_content_height(item, self.fonts[font_style])
            print(f"当前内容块高度: {content_height}, 当前Y位置: {current_y}")
            
            # 如果是标题且当前页面已经有内容，创建新页面
            if item['type'] == 'title' and current_content and current_y > self.margin:
                print("遇到新标题，创建新页面")
                if current_content:
                    images.append(self.create_single_image(current_content, background_path, font_style))
                    print(f"创建新页面，当前总页数: {len(images)}")
                    current_content = []
                    current_y = self.margin
            
            # 如果内容会超出页面
            if current_y + content_height > self.height - self.margin:
                print(f"内容超出页面: 需要 {current_y + content_height}, 最大高度 {self.height - self.margin}")
                if current_content:
                    remaining_height = self.height - self.margin - current_y
                    lines_per_page = self.calculate_lines_per_height(remaining_height, item['type'])
                    print(f"当前页剩余高度: {remaining_height}, 可容纳行数: {lines_per_page}")
                    
                    if lines_per_page > 0:
                        first_part, second_part = self.split_text_by_lines(
                            item['text'], 
                            self.fonts[font_style], 
                            lines_per_page,
                            item['type']
                        )
                        print(f"文本分割结果: 第一部分长度 {len(first_part) if first_part else 0}, "
                              f"第二部分长度 {len(second_part) if second_part else 0}")
                        
                        if first_part and first_part.strip():
                            current_content.append({
                                'type': item['type'],  # 保持原始类型
                                'text': first_part
                            })
                            print(f"添加第一部分到当前页面，类型: {item['type']}")
                    
                    if current_content:
                        images.append(self.create_single_image(current_content, background_path, font_style))
                        print(f"创建新页面，当前总页数: {len(images)}")
                    
                    current_content = []
                    current_y = self.margin
                    
                    if second_part and second_part.strip():
                        remaining_text = second_part
                        # 不改变索引，继续处理剩余文本
                        print(f"保存第二部分作为剩余文本，长度: {len(second_part)}")
                        continue
                else:
                    print("当前页面为空，强制分割内容")
                    lines_per_page = self.calculate_lines_per_height(
                        self.height - self.margin * 2, 
                        item['type']
                    )
                    first_part, second_part = self.split_text_by_lines(
                        item['text'],
                        self.fonts[font_style],
                        lines_per_page,
                        item['type']
                    )
                    
                    if first_part and first_part.strip():
                        current_content.append({
                            'type': item['type'],  # 保持原始类型
                            'text': first_part
                        })
                        images.append(self.create_single_image(current_content, background_path, font_style))
                        print(f"创建新页面，当前总页数: {len(images)}")
                        current_content = []
                        current_y = self.margin
                    
                    if second_part and second_part.strip():
                        remaining_text = second_part
                        # 不改变索引，继续处理剩余文本
                        print(f"保存第二部分作为剩余文本，长度: {len(second_part)}")
                        continue
                
                if not remaining_text:
                    print("无剩余文本，移动到下一个内容块")
                    i += 1
                    continue
            
            # 正常添加内容
            current_content.append(item)
            current_y += content_height
            print(f"添加内容到当前页面，更新Y位置: {current_y}")
            
            # 只有在没有剩余文本时才增加索引
            if not remaining_text:
                i += 1
        
        # 处理最后一页
        if current_content and any(item.get('text', '').strip() for item in current_content):
            images.append(self.create_single_image(current_content, background_path, font_style))
            print(f"添加最后一页，最终总页数: {len(images)}")
        
        print(f"\n处理完成，共生成 {len(images)} 页图片")
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
        
        # 重新组合文本，确保去除首尾空白
        first_part = '\n'.join(first_part_lines).strip()
        second_part = '\n'.join(second_part_lines).strip()
        
        # 如果分割后的部分为空，返回None
        if not first_part:
            first_part = None
        if not second_part:
            second_part = None
            
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
            current_font = ImageFont.truetype(font.path, font_size)
        except Exception as e:
            print(f"调整字体大小失败: {str(e)}")
            return 0
            
        # 获取换行后的文本
        max_width = self.width - (self.margin * 2)
        lines = self.get_wrapped_text(item['text'], current_font, max_width)
        
        # 计算总高度
        total_height = len(lines) * line_spacing
        
        # 添加段落间距
        total_height += line_spacing // 2
        
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
                    # 保存起始值
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
        lines = []
        # 处理列表格式
        processed_text = self.process_list_text(text)
        paragraphs = processed_text.split('\n')
        
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
                
                # 计算缩进和标记的宽度
                indent_marker_width = font.getlength(indent + marker)
                
                # 计算第一行可用宽度（减去缩进和标记的宽度）
                first_line_width = max_width - indent_marker_width
                
                # 处理第一行
                current_line = indent + marker
                current_width = indent_marker_width
                words = list(content)  # 按字符分割内容
                
                # 处理第一行剩余内容
                i = 0
                while i < len(words):
                    char_width = font.getlength(words[i])
                    if current_width + char_width <= max_width:
                        current_line += words[i]
                        current_width += char_width
                        i += 1
                    else:
                        break
                
                lines.append(current_line)
                
                # 处理后续行
                if i < len(words):
                    remaining_content = ''.join(words[i:])
                    # 计算后续行的缩进宽度（与第行标记对齐）
                    subsequent_indent = ' ' * (len(indent) + len(marker))
                    subsequent_indent_width = font.getlength(subsequent_indent)
                    
                    current_line = subsequent_indent
                    current_width = subsequent_indent_width
                    
                    for char in remaining_content:
                        char_width = font.getlength(char)
                        if current_width + char_width <= max_width:
                            current_line += char
                            current_width += char_width
                        else:
                            lines.append(current_line)
                            current_line = subsequent_indent + char
                            current_width = subsequent_indent_width + char_width
                    
                    if current_line != subsequent_indent:
                        lines.append(current_line)
            else:
                # 处理普通段落
                current_line = ''
                current_width = 0
                
                for char in paragraph:
                    char_width = font.getlength(char)
                    if current_width + char_width <= max_width:
                        current_line += char
                        current_width += char_width
                    else:
                        lines.append(current_line)
                        current_line = char
                        current_width = char_width
                
                if current_line:
                    lines.append(current_line)
        
        return lines
    
    def render_text(self, draw, text_content, font):
        """渲染文字到图片上"""
        current_y = self.margin
        max_width = self.width - (self.margin * 2)
        
        print(f"\n开始渲染文本，内容块数量: {len(text_content)}")
        
        for item in text_content:
            if not item.get('text', '').strip():
                print("跳过空内容块")
                continue
            
            print(f"\n渲染内容块:")
            print(f"类型: {item['type']}")
            print(f"内容长度: {len(item.get('text', ''))}")
            print(f"当前Y位置: {current_y}")
            
            # 设置不同类型文本的字体大小和样式
            if item['type'] == 'title':
                font_size = 48
                line_spacing = 60
                alignment = 'center'
            else:
                font_size = 32
                line_spacing = 45
                alignment = 'left'  # 非标题内容左对齐
            
            try:
                current_font = ImageFont.truetype(font.path, font_size)
            except Exception as e:
                print(f"调整字体大小失败: {str(e)}")
                continue
            
            # 获取换行后的文本
            lines = self.get_wrapped_text(item['text'], current_font, max_width)
            print(f"文本分行数: {len(lines)}")
            
            # 计算此内容块的总高度
            total_height = len(lines) * line_spacing
            print(f"内容块总高度: {total_height}")
            
            # 检查是否会超出页面底部
            if current_y + total_height > self.height - self.margin:
                print(f"警告：内容超出页面底部，跳过渲染。需要高度: {current_y + total_height}, 最大高度: {self.height - self.margin}")
                break
            
            # 渲染每一行
            for line_num, line in enumerate(lines):
                if not line:  # 空行处理
                    current_y += line_spacing // 2
                    print(f"空行处理，Y位置更新到: {current_y}")
                    continue
                
                # 计算文本位置
                if alignment == 'center':
                    # 标题居中
                    text_width = current_font.getlength(line)
                    x = (self.width - text_width) // 2
                    print(f"标题居中，X位置: {x}")
                else:
                    # 正文左对齐
                    x = self.margin
                    print(f"正文左对齐，X位置: {x}")
                
                try:
                    # 绘制文本
                    draw.text((x, current_y), line, font=current_font, fill='black')
                    print(f"渲染第 {line_num + 1} 行文本，位置: ({x}, {current_y})")
                    current_y += line_spacing
                except Exception as e:
                    print(f"渲染文本失败: {str(e)}")
            
            # 在不同文本块之间添加额外的间距
            current_y += line_spacing // 2
            print(f"添加额外间距，Y位置更新到: {current_y}")