from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QPushButton, 
                           QHBoxLayout, QComboBox, QLabel, QSpinBox, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal
import logging
import os
from datetime import datetime
import sys

class TextBlock(QWidget):
    deleted = pyqtSignal(object)  # 删除信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)  # 增加组件之间的间距

        # 类型选择
        self.type_combo = QComboBox()
        self.type_combo.addItems(["标题", "内容"])
        self.type_combo.setMinimumWidth(80)  # 设置最小宽度
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        layout.addWidget(self.type_combo)

        # 创建一个包含文本编辑框和删除按钮的容器
        editor_container = QWidget()
        editor_layout = QHBoxLayout(editor_container)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(5)

        # 文本编辑框
        self.editor = QTextEdit()
        # 启用自动换行，但使用单词边界
        self.editor.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.editor.setAcceptRichText(False)  # 只接受纯文本
        # 设置文本编辑框的样式
        self.editor.setStyleSheet("""
            QTextEdit {
                padding: 10px;
                margin: 0px;
                border: 1px solid #D9D9D9;
                border-radius: 4px;
                background-color: white;
                font-size: 14px;
            }
            QTextEdit:focus {
                border-color: #4096FF;
            }
        """)
        editor_layout.addWidget(self.editor)

        # 删除按钮
        delete_button = QPushButton("X")
        delete_button.setFixedSize(20, 20)  # 设置固定大小
        delete_button.clicked.connect(lambda: self.deleted.emit(self))
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #ff4d4f;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff7875;
            }
            QPushButton:pressed {
                background-color: #d9363e;
            }
        """)
        editor_layout.addWidget(delete_button)

        # 将容器添加到主布局
        layout.addWidget(editor_container)
        
        # 初始设置高度
        self.on_type_changed(self.type_combo.currentText())

    def on_type_changed(self, text):
        """根据类型调整编辑框高度"""
        if text == "标题":
            self.editor.setMinimumHeight(50)  # 减小标题最小高度
            self.editor.setMaximumHeight(50)  # 减小标题最大高度
            # 设置标题的字体大小
            self.editor.setStyleSheet("""
                QTextEdit {
                    padding: 8px;
                    margin: 0px;
                    border: 1px solid #D9D9D9;
                    border-radius: 4px;
                    background-color: white;
                    font-size: 12px;
                    font-weight: bold;
                }
                QTextEdit:focus {
                    border-color: #4096FF;
                }
            """)
        else:
            self.editor.setMinimumHeight(150)
            self.editor.setMaximumHeight(300)
            # 设置内容的字体大小
            self.editor.setStyleSheet("""
                QTextEdit {
                    padding: 10px;
                    margin: 0px;
                    border: 1px solid #D9D9D9;
                    border-radius: 4px;
                    background-color: white;
                    font-size: 12px;
                }
                QTextEdit:focus {
                    border-color: #4096FF;
                }
            """)

    def get_content(self):
        """获取文本内容，保留用户手动输入的换行符和前导空格"""
        # 获取原始文本内容
        text = self.editor.toPlainText()
        print("\n=== 获取文本内容 ===")
        print(f"原始文本:\n{repr(text)}")
        
        # 获取文档对象
        doc = self.editor.document()
        
        # 收集实际文本内容
        real_text = []
        block = doc.begin()
        while block.isValid():
            # 检查这个文本块是否是由软换行产生的
            if block.layout().lineCount() > 0:
                # 获取完整的文本行，包括前导空格
                line = block.text()
                print(f"块 {block.blockNumber()} 内容: {repr(line)}")
                
                # 只有当这个块是由用户手动换行产生的时候，才添加换行符
                if block.blockNumber() < doc.blockCount() - 1:
                    real_text.append(line + '\n')
                else:
                    real_text.append(line)
            block = block.next()
        
        # 合并文本
        final_text = ''.join(real_text)
        print(f"最终文本:\n{repr(final_text)}")
        
        return {
            'type': 'title' if self.type_combo.currentText() == "标题" else 'content',
            'text': final_text
        }

    def set_content(self, content):
        # 设置文本内容，保持原有的换行
        self.editor.setPlainText(content.get('text', ''))
        self.type_combo.setCurrentText("标题" if content.get('type') == 'title' else "内容")

class TextEditor(QWidget):
    content_changed = pyqtSignal()  # 内容变化信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.text_blocks = []
        self.init_ui()
        # 添加一个默认的标题文本块
        first_block = TextBlock()
        first_block.deleted.connect(self.remove_text_block)
        first_block.type_combo.setCurrentText("标题")  # 设置第一个文本块为标题类型
        self.text_blocks.append(first_block)
        self.blocks_layout.addWidget(first_block)

        # 添加一个默认的内容文本块
        second_block = TextBlock()
        second_block.deleted.connect(self.remove_text_block)
        second_block.type_combo.setCurrentText("内容")  # 设置第二个文本块为内容类型
        self.text_blocks.append(second_block)
        self.blocks_layout.addWidget(second_block)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 创建参数控制面板
        params_control = QWidget()
        params_layout = QHBoxLayout(params_control)  # 使用水平布局
        params_layout.setContentsMargins(0, 0, 0, 0)
        
        # 标题字号控制
        title_font_label = QLabel("标题字号：")
        self.title_font_spin = QSpinBox()
        self.title_font_spin.setFixedWidth(80)  # 设置固定宽度
        self.title_font_spin.setFixedHeight(30)
        self.title_font_spin.setRange(24, 120)
        self.title_font_spin.setValue(50)
        self.title_font_spin.setToolTip("调整标题文字的大小")
        
        params_layout.addWidget(title_font_label)
        params_layout.addWidget(self.title_font_spin)
        params_layout.addStretch()  # 添加弹性空间
        
        # 内容字号控制
        content_font_label = QLabel("内容字号：")
        self.content_font_spin = QSpinBox()
        self.content_font_spin.setFixedWidth(80)  # 设置固定宽度
        self.content_font_spin.setFixedHeight(30)
        self.content_font_spin.setRange(24, 96)
        self.content_font_spin.setValue(36)
        self.content_font_spin.setToolTip("调整内容文字的大小")
        
        params_layout.addWidget(content_font_label)
        params_layout.addWidget(self.content_font_spin)
        params_layout.addStretch()  # 添加弹性空间
        
        # 行间距控制
        line_spacing_label = QLabel("行间距：")
        self.line_spacing_spin = QSpinBox()
        self.line_spacing_spin.setFixedWidth(80)  # 设置固定宽度
        self.line_spacing_spin.setFixedHeight(30)
        self.line_spacing_spin.setRange(20, 200)
        self.line_spacing_spin.setValue(45)
        self.line_spacing_spin.setToolTip("调整行与行之间的间距")
        
        params_layout.addWidget(line_spacing_label)
        params_layout.addWidget(self.line_spacing_spin)
        params_layout.addStretch()  # 添加弹性空间
        
        # 将参数控制面板添加到主布局
        layout.addWidget(params_control)

        # 创建一个包含文本块和按钮的容器
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(10)

        # 创文本块容器
        self.blocks_container = QWidget()
        self.blocks_layout = QVBoxLayout(self.blocks_container)
        self.blocks_layout.setContentsMargins(0, 0, 0, 0)
        self.blocks_layout.setSpacing(10)
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidget(self.blocks_container)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 添加滚动区域到内容容器
        content_layout.addWidget(scroll)

        # 添加按钮容器
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加按钮
        add_button = QPushButton("添加文本块")
        add_button.setMinimumHeight(40)
        add_button.clicked.connect(self.add_text_block)
        button_layout.addWidget(add_button)
        
        # 将按钮容器添加到内容容器
        content_layout.addWidget(button_container)

        # 将内容容器添加到主布局
        layout.addWidget(content_container)

    def add_text_block(self):
        """添加新的文本块"""
        text_block = TextBlock()
        text_block.deleted.connect(self.remove_text_block)
        text_block.type_combo.setCurrentText("内容")  # 新增的文本块默认为内容类型
        self.text_blocks.append(text_block)
        self.blocks_layout.addWidget(text_block)
        self.content_changed.emit()

    def remove_text_block(self, block):
        if len(self.text_blocks) > 1:  # 保持至少一个文本块
            self.text_blocks.remove(block)
            block.deleteLater()
            self.content_changed.emit()

    def get_all_content(self):
        """获取所有内容，包括行间距和字体大小设置"""
        content = []
        
        # 设置日志
        logger = logging.getLogger('TextEditor')
        logger.setLevel(logging.DEBUG)
        
        # 检查是否已经有处理器
        if not logger.handlers:
            # 创建logs目录
            if not os.path.exists('logs'):
                os.makedirs('logs')
            
            # 生成日志文件名，包含时间戳
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_file = os.path.join('logs', f'text_editor_{timestamp}.log')
            
            # 添加文件处理器
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            
            # 添加控制台处理器
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG)
            
            # 设置日志格式
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        
        logger.info("=== 开始获取文本内容 ===")
        
        for i, block in enumerate(self.text_blocks):
            logger.info(f"\n处理文本块 {i+1}:")
            
            # 获取原始文本内容
            raw_text = block.editor.toPlainText()
            logger.info(f"原始文本内容: {repr(raw_text)}")
            
            # 统一换行符为 \n
            text = raw_text.replace('\r\n', '\n').replace('\r', '\n')
            
            # 处理每一行
            lines = text.split('\n')
            logger.info(f"分割后的行数: {len(lines)}")
            for j, line in enumerate(lines):
                logger.info(f"  行 {j+1}: {repr(line)}")
                logger.info(f"  行 {j+1} 长度: {len(line)}")
                logger.info(f"  行 {j+1} 前导空格数: {len(line) - len(line.lstrip())}")
            
            # 保留原始文本，包括前导空格，只去掉尾部空格
            text = '\n'.join(line.rstrip() for line in lines)
            logger.info(f"处理后的文本: {repr(text)}")
            
            item = {
                'type': 'title' if block.type_combo.currentText() == "标题" else 'content',
                'text': text,
                'line_spacing': self.line_spacing_spin.value()
            }
            
            if item['type'] == 'title':
                item['font_size'] = self.title_font_spin.value()
            else:
                item['font_size'] = self.content_font_spin.value()
            
            if text.strip():  # 只添加非空内容
                content.append(item)
                logger.info("文本块已添加到内容列表")
            else:
                logger.info("跳过空文本块")
        
        logger.info(f"\n=== 文本内容获取完成，共 {len(content)} 个内容块 ===")
        return content

    def set_all_content(self, content_list):
        # 清除现有的文本块
        while self.text_blocks:
            block = self.text_blocks.pop()
            block.deleteLater()

        # 添加新的文本块
        for content in content_list:
            text_block = TextBlock()
            text_block.set_content(content)
            text_block.deleted.connect(self.remove_text_block)
            self.text_blocks.append(text_block)
            self.blocks_layout.addWidget(text_block)

        # 如果没有内容，添加一个默认的文本块
        if not content_list:
            self.add_text_block()

        self.content_changed.emit()

    def clear(self):
        """清除所有文本块并添加一个空的"""
        self.set_all_content([])