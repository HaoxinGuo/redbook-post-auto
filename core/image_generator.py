from PIL import Image, ImageDraw, ImageFont
import os
import textwrap

class ImageGenerator:
    def __init__(self):
        self.width = 1080
        self.height = 1440  # 3:4 比例
        self.fonts = self.load_fonts()
        self.margin = 50  # 边距
        
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

    def get_wrapped_text(self, text, font, max_width):
        """将文本按照最大宽度换行"""
        lines = []
        # 如果文本中已经有换行符，先按换行符分割
        paragraphs = text.split('\n')
        
        for paragraph in paragraphs:
            if not paragraph:
                lines.append('')
                continue
                
            # 计算每个字符的平均宽度
            avg_char_width = font.getlength("测") # 使用中文字符作为参考
            
            # 计算每行大约可以容纳多少字符
            chars_per_line = int(max_width / avg_char_width)
            
            # 将段落按照计算出的字符数分行
            while paragraph:
                line = paragraph[:chars_per_line]
                # 确保行宽度不超过最大宽度
                while font.getlength(line) > max_width and len(line) > 1:
                    line = line[:-1]
                lines.append(line)
                paragraph = paragraph[len(line):]
        
        return lines
        
    def render_text(self, draw, text_content, font):
        """渲染文字到图片上"""
        current_y = self.margin
        max_width = self.width - (self.margin * 2)  # 考虑左右边距
        
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
            
            # 调整字体大小
            try:
                if item['type'] == 'title':
                    current_font = ImageFont.truetype(font.path, font_size)
                else:
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
                    
                # 计算文本宽度用于居中（仅标题居中）
                if item['type'] == 'title':
                    text_width = current_font.getlength(line)
                    x = (self.width - text_width) // 2
                else:
                    x = self.margin
                
                # 绘制文本
                draw.text((x, current_y), line, font=current_font, fill='black')
                current_y += line_spacing
            
            # 在不同文本块之间添加额外的间距
            current_y += line_spacing
            
            # 检查是否超出图片高度
            if current_y > self.height - self.margin:
                break