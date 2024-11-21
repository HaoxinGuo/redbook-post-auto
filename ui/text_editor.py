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

        # 创建一个包含文本编辑框和按钮的容器
        editor_container = QWidget()
        editor_layout = QHBoxLayout(editor_container)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(5)

        # 文本编辑框
        self.editor = QTextEdit()
        self.editor.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.editor.setAcceptRichText(True)  # 允许富文本
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

        # 创建按钮容器
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(5)

        # 颜色选择按钮
        self.color_button = QPushButton("文字颜色")
        self.color_button.setFixedSize(80, 30)
        self.color_button.clicked.connect(self.choose_color)
        self.color_button.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                border-color: #4096ff;
                color: #4096ff;
            }
        """)
        button_layout.addWidget(self.color_button)

        # 删除按钮
        delete_button = QPushButton("删除")
        delete_button.setFixedSize(40, 30)
        delete_button.clicked.connect(lambda: self.deleted.emit(self))
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #ff7875;
            }
            QPushButton:pressed {
                background-color: #d9363e;
            }
        """)
        button_layout.addWidget(delete_button)

        # 将按钮容器添加到编辑器布局
        editor_layout.addWidget(button_container)

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
        """获取文本内容，包括颜色信息"""
        doc = self.editor.document()
        text = ""
        colors = []
        current_position = 0
        
        print("\n=== 获取文本内容和颜色信息 ===")
        print(f"文本块类型: {self.type_combo.currentText()}")
        
        for block_num in range(doc.blockCount()):
            block = doc.findBlockByNumber(block_num)
            block_text = block.text()
            block_length = len(block_text)
            
            print(f"\n处理文本块 {block_num + 1}:")
            print(f"块文本: '{block_text}'")
            
            # 处理块内的每个字符
            for i in range(block_length):
                cursor = self.editor.textCursor()
                cursor.setPosition(block.position() + i)
                cursor.movePosition(cursor.MoveOperation.Right, cursor.MoveMode.KeepAnchor)
                
                char_format = cursor.charFormat()
                if char_format.foreground().style() != 0:  # 检查是否设置了前景色
                    color = char_format.foreground().color()
                    if color.isValid() and color.name() != '#000000':
                        # 尝试合并连续的相同颜色
                        if colors and colors[-1]['color'] == color.name() and \
                           colors[-1]['end'] == current_position + i:
                            colors[-1]['end'] = current_position + i + 1
                        else:
                            color_info = {
                                'start': current_position + i,
                                'end': current_position + i + 1,
                                'color': color.name()
                            }
                            colors.append(color_info)
                            print(f"发现字符颜色: {color.name()} at position {current_position + i}")
            
            # 更新位置计数器
            if block_num < doc.blockCount() - 1:
                text += block_text + '\n'
                current_position += block_length + 1
                print("添加换行符，位置更新")
            else:
                text += block_text
                current_position += block_length
        
        # 合并连续的相同颜色区域
        merged_colors = []
        for color_info in colors:
            if merged_colors and merged_colors[-1]['color'] == color_info['color'] and \
               merged_colors[-1]['end'] == color_info['start']:
                merged_colors[-1]['end'] = color_info['end']
            else:
                merged_colors.append(color_info)
        
        print(f"\n最终文本: '{text}'")
        print(f"颜色信息: {merged_colors}")
        print("=== 内容获取完成 ===\n")
        
        return {
            'type': 'title' if self.type_combo.currentText() == "标题" else 'content',
            'text': text,
            'colors': merged_colors,
            'line_spacing': 45
        }

    def set_content(self, content):
        """设置文本内容，恢复颜色信息"""
        from PyQt6.QtGui import QTextCharFormat, QColor
        
        self.editor.setPlainText(content.get('text', ''))
        self.type_combo.setCurrentText("标题" if content.get('type') == 'title' else "内容")
        
        # 恢复颜色信息
        for color_info in content.get('colors', []):
            cursor = self.editor.textCursor()
            cursor.setPosition(color_info['start'])
            cursor.setPosition(color_info['end'], cursor.MoveMode.KeepAnchor)
            
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color_info['color']))
            cursor.mergeCharFormat(fmt)

    def choose_color(self):
        """打开颜色选择对话框并设置所选文本的颜色"""
        from PyQt6.QtWidgets import QColorDialog
        from PyQt6.QtGui import QTextCharFormat, QColor
        
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            print("没有选中文本，无法设置颜色")
            return
        
        # 获取选中的文本范围
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        print(f"\n=== 设置文本颜色 ===")
        print(f"选中文本范围: {start}-{end}")
        print(f"选中文本内容: '{cursor.selectedText()}'")
        
        color = QColorDialog.getColor()
        if color.isValid():
            print(f"选择的颜色: {color.name()}")
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            
            # 只对选中的文本应用颜色
            cursor.mergeCharFormat(fmt)
            print("颜色设置成功")
        else:
            print("取消颜色选择")

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
        """获取所有内容，包括颜色信息"""
        content = []
        for block in self.text_blocks:
            block_content = block.get_content()
            if block_content['text'].strip():  # 只添加非内容
                content.append(block_content)
        return content

    def set_all_content(self, content_list):
        """设置所有内容，恢复颜色信息"""
        # 清除现有的文本块
        while self.text_blocks:
            block = self.text_blocks.pop()
            block.deleteLater()
        
        # 添加新的文本块
        for content in content_list:
            text_block = TextBlock()
            text_block.set_content(content)  # 包含颜色信息的恢复
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