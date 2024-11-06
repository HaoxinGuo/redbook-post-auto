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
        return fonts
        
    def create_images(self, text_content, background_path, font_style='normal'):
        """生成多页图片"""
        images = []
        remaining_content = text_content.copy()
        current_page_content = []
        current_y = self.margin
        
        print("\n=== 开始生成图片 ===")
        print(f"总内容块数: {len(text_content)}")
        
        while remaining_content:
            print(f"\n--- 处理新页面 ---")
            print(f"当前Y位置: {current_y}")
            print(f"剩余内容块数: {len(remaining_content)}")
            
            # 获取下一个内容块
            item = remaining_content[0]
            print(f"\n处理内容块:")
            print(f"类型: {item['type']}")
            print(f"内容长度: {len(item.get('text', ''))}")
            print(f"内容: {item.get('text', '')[:50]}...")
            
            if not item.get('text', '').strip():
                print("跳过空内容块")
                remaining_content.pop(0)
                continue
            
            # 使用内容块自带的字体大小
            font_size = item.get('font_size')
            if font_size is None:
                font_size = 48 if item['type'] == 'title' else 32
                print(f"使用默认字体大小: {font_size}")
            else:
                print(f"使用自定义字体大小: {font_size}")
            
            line_spacing = item.get('line_spacing', 45)
            print(f"行间距: {line_spacing}")
            
            try:
                current_font = ImageFont.truetype(self.fonts[font_style].path, font_size)
                print("字体加载成功")
            except Exception as e:
                print(f"字体加载失败: {str(e)}")
                remaining_content.pop(0)
                continue
            
            # 获取换行后的文本
            lines = self.get_wrapped_text(item['text'], current_font, self.width - (self.margin * 2))
            content_height = len(lines) * line_spacing + line_spacing // 2
            print(f"内容分行数: {len(lines)}")
            print(f"内容需要高度: {content_height}")
            print(f"当前页面剩余高度: {self.height - current_y - self.margin}")
            
            # 检查是否需要分页
            if current_y + content_height > self.height - self.margin:
                print("\n内容超出当前页面")
                
                # 计算当前页面剩余可用行数
                available_height = self.height - current_y - self.margin
                max_lines = available_height // line_spacing
                print(f"当前页面可容纳行数: {max_lines}")
                
                if max_lines > 0 and (not current_page_content or item['type'] != 'title'):
                    # 分割内容
                    first_part = {
                        'type': item['type'],
                        'text': '\n'.join(lines[:max_lines]),
                        'line_spacing': line_spacing,
                        'font_size': font_size  # 保持字体大小
                    }
                    second_part = {
                        'type': item['type'],
                        'text': '\n'.join(lines[max_lines:]),
                        'line_spacing': line_spacing,
                        'font_size': font_size  # 保持字体大小
                    }
                    
                    print(f"分割为两部分:")
                    print(f"第一部分长度: {len(first_part['text'])}")
                    print(f"第二部分长度: {len(second_part['text'])}")
                    
                    if first_part['text'].strip():
                        current_page_content.append(first_part)
                        print("添加第一部分到当前页面")
                    
                    if second_part['text'].strip():
                        remaining_content[0] = second_part
                        print("保存第二部分到剩余内容")
                    else:
                        remaining_content.pop(0)
                
                # 创建当前页面
                if current_page_content:
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
                    print("开始渲染当前页面内容")
                    self.render_text(draw, current_page_content, self.fonts[font_style])
                    images.append(image)
                    print(f"页面完成，当前总页数: {len(images)}")
                    
                    # 重置当前页面
                    current_page_content = []
                    current_y = self.margin
                    print("重置页面状态")
                
                continue
            
            # 添加内容到当前页面
            print("\n添加内容到当前页面")
            current_page_content.append(item)
            current_y += content_height
            remaining_content.pop(0)
            print(f"当前页面内容块数: {len(current_page_content)}")
            print(f"更新后的Y位置: {current_y}")
        
        # 处理最后一页
        if current_page_content:
            print("\n处理最后一页")
            print(f"最后一页内容块数: {len(current_page_content)}")
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
            self.render_text(draw, current_page_content, self.fonts[font_style])
            images.append(image)
            print(f"最后一页完成，最终总页数: {len(images)}")
        
        print("\n=== 图片生成完成 ===")
        print(f"总页数: {len(images)}")
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
            
            # 获取换行后的文本
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
        
        # 重组合文本，确保去除首尾空白
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
                
                # 计算第一行可用宽���（减去缩进和标记的宽度）
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
        
        print(f"\n=== 开始渲染文本 ===")
        print(f"总内容块数: {len(text_content)}")
        
        # 获取第一个内容块的行间距作为统一行间距
        global_line_spacing = None
        for item in text_content:
            if item.get('text', '').strip() and item['type'] == 'content':
                global_line_spacing = item.get('line_spacing', 45)
                print(f"使用全局行间距: {global_line_spacing}")
                break
        
        if global_line_spacing is None:
            global_line_spacing = 45  # 如果没有找到内容块，使用默认值
            print(f"使用默认行间距: {global_line_spacing}")
        
        # 计算当前页面已使用的高度
        total_height = 0
        
        for item in text_content:
            if not item.get('text', '').strip():
                print("跳过空内容块")
                continue
            
            print(f"\n--- 渲染内容块 ---")
            print(f"类型: {item['type']}")
            print(f"内容: {item.get('text', '')[:50]}...")
            print(f"当前Y位置: {current_y}")
            
            # 使用内容块自带的字体大小
            font_size = item.get('font_size')
            if font_size is None:
                font_size = 48 if item['type'] == 'title' else 32
                print(f"使用默认字体大小: {font_size}")
            else:
                print(f"使用自定义字体大小: {font_size}")
            
            # 使用统一的行间距
            line_spacing = global_line_spacing
            print(f"使用行间距: {line_spacing}")
            alignment = 'center' if item['type'] == 'title' else 'left'
            print(f"对齐方式: {alignment}")
            
            try:
                print(f"尝试加载字体: {font.path}, 大小: {font_size}")
                current_font = ImageFont.truetype(font.path, font_size)
                print("字体加载成功")
            except Exception as e:
                print(f"字体加载失败: {str(e)}")
                continue
            
            # 获取换行后的文本
            lines = self.get_wrapped_text(item['text'], current_font, max_width)
            print(f"文本分行数: {len(lines)}")
            
            # 计算此内容块的总高度
            block_height = len(lines) * line_spacing
            total_height += block_height
            print(f"内容块总高度: {block_height}")
            print(f"当前总高度: {total_height}")
            
            # 检查是否会超出页面底部
            if total_height > self.height - self.margin * 2:
                print(f"警告：内容超出页面底部，需要分页")
                print(f"需要总高度: {total_height}")
                print(f"最大可用高度: {self.height - self.margin * 2}")
                return False
            
            # 渲染每一行
            for line_num, line in enumerate(lines):
                if not line:
                    current_y += line_spacing // 2
                    print(f"空行处理，Y位置更新到: {current_y}")
                    continue
                
                # 计算文本位置
                if alignment == 'center':
                    text_width = current_font.getlength(line)
                    x = (self.width - text_width) // 2
                    print(f"标题居中，X位置: {x}")
                else:
                    x = self.margin
                    print(f"正文左对齐，X位置: {x}")
                
                try:
                    print(f"渲染第 {line_num + 1} 行文本:")
                    print(f"位置: ({x}, {current_y})")
                    print(f"内容: {line}")
                    print(f"字体大小: {font_size}")
                    draw.text((x, current_y), line, font=current_font, fill='black')
                    current_y += line_spacing
                except Exception as e:
                    print(f"渲染文本失败: {str(e)}")
            
            # 在不同文本块之间添加额外的间距（使用统一行间距）
            if item != text_content[-1]:  # 如果不是最后一个内容块
                current_y += line_spacing // 2
                total_height += line_spacing // 2
                print(f"添加额外间距，Y位置更新到: {current_y}")
        
        print("\n=== 渲染完成 ===")
        return True

    def draw_styled_text(self, draw, text, marks, x, y, font, char_spacing=0, line_spacing=20):
        """绘制带样式的文本"""
        char_width = font.getlength("测")  # 使用一个汉字宽度作为参考
        line_height = font.size + line_spacing  # 行高等于字体大小加行间距
        
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
            
            # 收集每行的下划线��息
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