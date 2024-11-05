from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QPushButton, 
                           QHBoxLayout, QComboBox, QLabel)
from PyQt6.QtCore import Qt, pyqtSignal

class TextBlock(QWidget):
    deleted = pyqtSignal(object)  # 删除信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 类型选择
        self.type_combo = QComboBox()
        self.type_combo.addItems(["标题", "内容"])
        layout.addWidget(self.type_combo)

        # 文本编辑框
        self.editor = QTextEdit()
        self.editor.setMinimumHeight(50)
        self.editor.setMaximumHeight(100)
        layout.addWidget(self.editor)

        # 按钮容器
        button_layout = QVBoxLayout()
        
        # 删除按钮
        delete_button = QPushButton("×")
        delete_button.setMaximumWidth(30)
        delete_button.clicked.connect(lambda: self.deleted.emit(self))
        button_layout.addWidget(delete_button)
        
        layout.addLayout(button_layout)

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
        self.layout = QVBoxLayout(self)
        
        # 添加按钮
        add_button = QPushButton("添加文本块")
        add_button.clicked.connect(self.add_text_block)
        self.layout.addWidget(add_button)

        # 添加一个默认的文本块
        self.add_text_block()

        # 添加弹性空间
        self.layout.addStretch()

    def add_text_block(self):
        text_block = TextBlock()
        text_block.deleted.connect(self.remove_text_block)
        self.text_blocks.append(text_block)
        # 在弹性空间之前插入新的文本块
        self.layout.insertWidget(len(self.text_blocks), text_block)
        self.content_changed.emit()

    def remove_text_block(self, block):
        if len(self.text_blocks) > 1:  # 保持至少一个文本块
            self.text_blocks.remove(block)
            block.deleteLater()
            self.content_changed.emit()

    def get_all_content(self):
        return [block.get_content() for block in self.text_blocks]

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
            self.layout.insertWidget(len(self.text_blocks), text_block)

        # 如果没有内容，添加一个默认的文本块
        if not content_list:
            self.add_text_block()

        self.content_changed.emit()

    def clear(self):
        """清除所有文本块并添加一个空的"""
        self.set_all_content([]) 