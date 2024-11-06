from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QPushButton, 
                           QHBoxLayout, QComboBox, QLabel, QSpinBox, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal

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
        # 设置文本编辑框的样式
        self.editor.setStyleSheet("""
            QTextEdit {
                padding: 10px;
                line-height: 1.5;
                font-size: 14px;
            }
        """)
        editor_layout.addWidget(self.editor)

        # 删除按钮
        delete_button = QPushButton("×")
        delete_button.setFixedSize(24, 24)  # 设置固定大小
        delete_button.clicked.connect(lambda: self.deleted.emit(self))
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #ff4d4f;
                color: white;
                border: none;
                border-radius: 12px;
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
            self.editor.setMinimumHeight(20)  # 减小标题最小高度
            self.editor.setMaximumHeight(50)  # 减小标题最大高度
            # 设置标题的字体大小
            self.editor.setStyleSheet("""
                QTextEdit {
                    padding: 8px;  # 减小内边距
                    line-height: 1.3;  # 减小行高
                    font-size: 48px;
                    font-weight: bold;
                }
            """)
        else:
            self.editor.setMinimumHeight(150)
            self.editor.setMaximumHeight(300)
            # 设置内容的字体大小
            self.editor.setStyleSheet("""
                QTextEdit {
                    padding: 10px;
                    line-height: 1.5;
                    font-size: 12px;
                }
            """)

    def get_content(self):
        return {
            'type': 'title' if self.type_combo.currentText() == "标题" else 'content',
            'text': self.editor.toPlainText()
        }

    def set_content(self, content):
        self.type_combo.setCurrentText("标题" if content['type'] == 'title' else "内容")
        self.editor.setPlainText(content['text'])

class TextEditor(QWidget):
    content_changed = pyqtSignal()  # 内容变化信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.text_blocks = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 添加行间距控制
        spacing_control = QWidget()
        spacing_layout = QHBoxLayout(spacing_control)
        spacing_layout.setContentsMargins(0, 0, 0, 0)
        
        line_spacing_label = QLabel("行间距：")
        self.line_spacing_spin = QSpinBox()
        self.line_spacing_spin.setRange(20, 200)  # 行间距范围20-200像素
        self.line_spacing_spin.setValue(45)  # 默认值45
        self.line_spacing_spin.setToolTip("调整行与行之间的间距")
        
        spacing_layout.addWidget(line_spacing_label)
        spacing_layout.addWidget(self.line_spacing_spin)
        spacing_layout.addStretch()
        
        layout.addWidget(spacing_control)

        # 创建一个包含文本块和按钮的容器
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(10)

        # 创建文本块容器
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

        # 添加一个默认的文本块
        self.add_text_block()

    def add_text_block(self):
        """添加新的文本块"""
        text_block = TextBlock()
        text_block.deleted.connect(self.remove_text_block)
        self.text_blocks.append(text_block)
        self.blocks_layout.addWidget(text_block)
        self.content_changed.emit()

    def remove_text_block(self, block):
        if len(self.text_blocks) > 1:  # 保持至少一个文本块
            self.text_blocks.remove(block)
            block.deleteLater()
            self.content_changed.emit()

    def get_all_content(self):
        """获取所有内容，包括行间距设置"""
        content = [block.get_content() for block in self.text_blocks]
        # 添加行间距信息
        for item in content:
            item['line_spacing'] = self.line_spacing_spin.value()
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