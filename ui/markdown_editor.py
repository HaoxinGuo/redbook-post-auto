from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QFileDialog, QTextEdit, QLabel)
from PyQt6.QtCore import pyqtSignal
import markdown
import os

class MarkdownEditor(QWidget):
    content_changed = pyqtSignal()  # 内容变化信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 创建顶部按钮区域
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        
        # 创建打开文件按钮
        self.open_button = QPushButton("打开Markdown文件")
        self.open_button.setMinimumHeight(40)
        self.open_button.clicked.connect(self.open_markdown_file)
        
        # 创建刷新按钮
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.setMinimumHeight(40)
        self.refresh_button.clicked.connect(self.refresh_content)
        self.refresh_button.setEnabled(False)
        
        # 添加按钮到布局
        button_layout.addWidget(self.open_button)
        button_layout.addWidget(self.refresh_button)
        button_layout.addStretch()
        
        # 添加文件路径显示标签
        self.file_label = QLabel()
        
        # 创建预览区域
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        
        # 添加所有组件到主布局
        layout.addWidget(button_container)
        layout.addWidget(self.file_label)
        layout.addWidget(self.preview)

    def open_markdown_file(self):
        """打开Markdown文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择Markdown文件",
            "",
            "Markdown Files (*.md);;All Files (*)"
        )
        
        if file_path:
            self.current_file = file_path
            self.file_label.setText(f"当前文件: {os.path.basename(file_path)}")
            self.refresh_button.setEnabled(True)
            self.load_markdown()

    def refresh_content(self):
        """刷新内容"""
        if self.current_file:
            self.load_markdown()

    def load_markdown(self):
        """加载并解析Markdown文件"""
        try:
            with open(self.current_file, 'r', encoding='utf-8') as f:
                markdown_text = f.read()
            
            # 将Markdown转换为HTML以便预览
            html = markdown.markdown(markdown_text)
            self.preview.setHtml(html)
            
            # 解析Markdown内容为文本编辑器格式
            content = self.parse_markdown_to_content(markdown_text)
            self.content = content
            self.content_changed.emit()
            
        except Exception as e:
            self.preview.setPlainText(f"加载文件失败: {str(e)}")

    def parse_markdown_to_content(self, markdown_text):
        """将Markdown文本解析为内容块列表"""
        content = []
        current_text = []
        is_title = False
        
        lines = markdown_text.split('\n')
        
        def process_inline_styles(text):
            """处理行内样式（加粗和倾斜）"""
            # 存储样式标记
            marks = {}
            processed_text = ""
            current_pos = 0
            
            # 处理加粗 (**text** 或 __text__)
            bold_pattern = r'\*\*(.*?)\*\*|__(.*?)__'
            # 处理倾斜 (*text* 或 _text_)
            italic_pattern = r'\*((?!\*).+?)\*|_((?!_).+?)_'
            
            # 先处理加粗
            import re
            text_parts = []
            last_end = 0
            
            for match in re.finditer(bold_pattern, text):
                bold_text = match.group(1) or match.group(2)
                start_pos = len(processed_text + text[last_end:match.start()])
                
                # 添加匹配之前的文本
                text_parts.append(text[last_end:match.start()])
                # 添加加粗文本
                text_parts.append(bold_text)
                
                # 记录加粗样式
                end_pos = start_pos + len(bold_text) - 1
                marks[(start_pos, end_pos)] = {'type': 'bold'}
                
                last_end = match.end()
            
            text_parts.append(text[last_end:])
            text = ''.join(text_parts)
            
            # 再处理倾斜
            text_parts = []
            last_end = 0
            processed_text = ""
            
            for match in re.finditer(italic_pattern, text):
                italic_text = match.group(1) or match.group(2)
                start_pos = len(processed_text + text[last_end:match.start()])
                
                # 添加匹配之前的文本
                text_parts.append(text[last_end:match.start()])
                # 添加倾斜文本
                text_parts.append(italic_text)
                
                # 记录倾斜样式
                end_pos = start_pos + len(italic_text) - 1
                marks[(start_pos, end_pos)] = {'type': 'italic'}
                
                last_end = match.end()
                processed_text += text[last_end:match.start()] + italic_text
            
            text_parts.append(text[last_end:])
            final_text = ''.join(text_parts)
            
            return final_text, marks
        
        for line in lines:
            # 检测标题
            if line.startswith('#'):
                # 如果之前有内容，先保存
                if current_text:
                    text = '\n'.join(current_text).strip()
                    processed_text, marks = process_inline_styles(text)
                    content.append({
                        'type': 'title' if is_title else 'content',
                        'text': processed_text,
                        'marks': marks
                    })
                    current_text = []
                
                # 移除 # 号并保存标题
                title = line.lstrip('#').strip()
                processed_title, title_marks = process_inline_styles(title)
                content.append({
                    'type': 'title',
                    'text': processed_title,
                    'marks': title_marks
                })
                is_title = False
                
            else:
                # 处理普通文本
                if line.strip():
                    current_text.append(line)
                elif current_text:
                    # 遇到空行时保存当前文本块
                    text = '\n'.join(current_text).strip()
                    processed_text, marks = process_inline_styles(text)
                    content.append({
                        'type': 'title' if is_title else 'content',
                        'text': processed_text,
                        'marks': marks
                    })
                    current_text = []
                    is_title = False
        
        # 保存最后的文本块
        if current_text:
            text = '\n'.join(current_text).strip()
            processed_text, marks = process_inline_styles(text)
            content.append({
                'type': 'title' if is_title else 'content',
                'text': processed_text,
                'marks': marks
            })
        
        return content

    def get_all_content(self):
        """获取所有内容，格式与TextEditor兼容"""
        if not hasattr(self, 'content'):
            return []
        
        # 为每个内容块添加默认的样式参数
        for item in self.content:
            if item['type'] == 'title':
                item['font_size'] = 48
                item['line_spacing'] = 60
            else:
                item['font_size'] = 32
                item['line_spacing'] = 45
            
            # 处理加粗和倾斜样式
            marks = item.get('marks', {})
            for (start, end), style in list(marks.items()):
                if style['type'] == 'bold':
                    # 将加粗样式转换为字体加粗
                    item['font_bold'] = True
                elif style['type'] == 'italic':
                    # 将倾斜样式转换为椭圆标记
                    marks[(start, end)] = {
                        'type': 'ellipse',
                        'position': 0,
                        'size': 15,
                        'width': 2,
                        'color': '#ffaa7f'
                    }
        
        return self.content 