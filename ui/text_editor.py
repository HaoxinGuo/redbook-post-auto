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

        # 文本编辑框
        self.editor = QTextEdit()
        self.editor.setMinimumHeight(100)  # 增加最小高度
        self.editor.setMaximumHeight(300)  # 增加最大高度
        # 设置文本编辑框的样式
        self.editor.setStyleSheet("""
            QTextEdit {
                padding: 10px;
                line-height: 1.5;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.editor)

        # 按钮容器
        button_layout = QVBoxLayout()
        button_layout.setSpacing(5)
        
        # 删除按钮
        delete_button = QPushButton("×")
        delete_button.setMaximumWidth(40)
        delete_button.setMinimumHeight(40)
        delete_button.clicked.connect(lambda: self.deleted.emit(self))
        button_layout.addWidget(delete_button)
        button_layout.addStretch()  # 添加弹性空间
        
        layout.addLayout(button_layout)
        
        # 初始设置高度
        self.on_type_changed(self.type_combo.currentText())

    def on_type_changed(self, text):
        """根据类型调整编辑框高度"""
        if text == "标题":
            self.editor.setMinimumHeight(80)
            self.editor.setMaximumHeight(150)
            # 设置标题的字体大小
            self.editor.setStyleSheet("""
                QTextEdit {
                    padding: 10px;
                    line-height: 1.5;
                    font-size: 16px;
                    font-weight: bold;
                }
            """)
        else:
            self.editor.setMinimumHeight(150)
            self.editor.setMaximumHeight(400)
            # 设置内容的字体大小
            self.editor.setStyleSheet("""
                QTextEdit {
                    padding: 10px;
                    line-height: 1.5;
                    font-size: 14px;
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

        # 文本编辑区域
        self.text_blocks = []
        self.init_text_blocks(layout)

        # 添加按钮容器
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加按钮
        add_button = QPushButton("添加文本块")
        add_button.setMinimumHeight(40)
        add_button.clicked.connect(self.add_text_block)
        button_layout.addWidget(add_button)
        
        layout.addWidget(button_container)

        # 添加一个默认的文本块
        self.add_text_block()

        # 添加弹性空间
        layout.addStretch()

    def init_text_blocks(self, layout):
        """初始化文本块区域"""
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
        
        # 添加到主布局
        layout.addWidget(scroll)

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