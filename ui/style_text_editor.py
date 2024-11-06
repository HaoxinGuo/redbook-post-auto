from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                           QPushButton, QLabel, QScrollArea, QSpinBox, QCheckBox,
                           QColorDialog, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QKeyEvent, QColor

class StyleTextEditor(QWidget):
    content_changed = pyqtSignal()
    style_applied = pyqtSignal()
    font_changed = pyqtSignal()  # 新增字体变化信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.text_marks = {}
        self.selected_chars = set()
        self.last_selected_index = None
        self.shift_pressed = False
        self.ctrl_pressed = False
        self.font_size = 96  # 默认字号
        self.font_bold = False  # 默认不加粗
        self.current_color = '#000000'  # 椭圆默认颜色
        self.underline_current_color = '#000000'  # 下划线默认颜色
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 添加字体控制面板
        font_control = QWidget()
        font_control_layout = QHBoxLayout(font_control)
        font_control_layout.setContentsMargins(0, 0, 0, 0)
        
        # 字号控制
        font_size_label = QLabel("字体大小：")
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(12, 200)  # 设置字号范围
        self.font_size_spin.setValue(self.font_size)
        self.font_size_spin.valueChanged.connect(self.on_font_size_changed)
        
        # 加粗控制
        self.bold_checkbox = QCheckBox("加粗")
        self.bold_checkbox.setChecked(self.font_bold)
        self.bold_checkbox.stateChanged.connect(self.on_bold_changed)
        
        font_control_layout.addWidget(font_size_label)
        font_control_layout.addWidget(self.font_size_spin)
        font_control_layout.addWidget(self.bold_checkbox)
        font_control_layout.addStretch()
        
        layout.addWidget(font_control)

        # 设置默认字体
        self.default_font = QFont("Microsoft YaHei UI", 12)  # 使用微软雅黑字体
        self.setFont(self.default_font)

        # 文本编辑区
        self.text_edit = QTextEdit()
        self.text_edit.setMinimumHeight(100)
        self.text_edit.textChanged.connect(self.on_text_changed)
        self.text_edit.selectionChanged.connect(self.on_selection_changed)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                padding: 10px;
                line-height: 1.5;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.text_edit)

        # 直接添加样式按钮
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)

        self.underline_button = QPushButton("添加下划线")
        self.underline_button.setEnabled(False)
        self.circle_button = QPushButton("添加圆圈")
        self.circle_button.setEnabled(False)
        self.ellipse_button = QPushButton("添加强调椭圆")
        self.ellipse_button.setEnabled(False)
        self.clear_button = QPushButton("清除样式")
        self.clear_button.setEnabled(False)

        button_layout.addWidget(self.underline_button)
        button_layout.addWidget(self.circle_button)
        button_layout.addWidget(self.ellipse_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()

        layout.addWidget(button_container)

        # 设置焦点策略，使组件能够接收键盘事件
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # 添加分隔线
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.HLine)
        separator1.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator1)

        # 添加样式控制区域标题
        style_control_title = QLabel("样式控制：")
        style_control_title.setFont(QFont("Microsoft YaHei UI", 12, QFont.Weight.Bold))
        layout.addWidget(style_control_title)

        # 椭圆控制面板
        ellipse_title = QLabel("椭圆样式控制：")
        layout.addWidget(ellipse_title)

        self.ellipse_control = QWidget()
        ellipse_control_layout = QHBoxLayout(self.ellipse_control)
        ellipse_control_layout.setContentsMargins(0, 0, 0, 0)
        
        # 椭圆控制选项
        position_label = QLabel("位置：")
        self.position_spin = QSpinBox()
        self.position_spin.setRange(-20, 20)
        self.position_spin.setValue(0)
        self.position_spin.setToolTip("调整椭圆的垂直位置")
        
        size_label = QLabel("大小：")
        self.size_spin = QSpinBox()
        self.size_spin.setRange(5, 100)
        self.size_spin.setValue(30)
        self.size_spin.setToolTip("调整椭圆的大小")
        
        width_label = QLabel("粗细：")
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 100)
        self.width_spin.setValue(5)
        self.width_spin.setToolTip("调整椭圆线条的粗细")
        
        self.color_button = QPushButton("选择颜色")
        self.color_button.clicked.connect(self.choose_color)  # 连接颜色选择事件
        
        ellipse_control_layout.addWidget(position_label)
        ellipse_control_layout.addWidget(self.position_spin)
        ellipse_control_layout.addWidget(size_label)
        ellipse_control_layout.addWidget(self.size_spin)
        ellipse_control_layout.addWidget(width_label)
        ellipse_control_layout.addWidget(self.width_spin)
        ellipse_control_layout.addWidget(QLabel("颜色："))
        ellipse_control_layout.addWidget(self.color_button)
        ellipse_control_layout.addStretch()
        
        layout.addWidget(self.ellipse_control)

        # 下划线控制面板
        underline_title = QLabel("下划线样式控制：")
        layout.addWidget(underline_title)

        self.underline_control = QWidget()
        underline_control_layout = QHBoxLayout(self.underline_control)
        underline_control_layout.setContentsMargins(0, 0, 0, 0)
        
        # 下划线控制选项
        underline_width_label = QLabel("粗细：")
        self.underline_width_spin = QSpinBox()
        self.underline_width_spin.setRange(1, 50)
        self.underline_width_spin.setValue(2)
        self.underline_width_spin.setToolTip("调整下划线的粗细")
        
        underline_offset_label = QLabel("距离：")
        self.underline_offset_spin = QSpinBox()
        self.underline_offset_spin.setRange(0, 50)
        self.underline_offset_spin.setValue(5)
        self.underline_offset_spin.setToolTip("调整下划线与文字的距离")
        
        self.underline_color_button = QPushButton("选择颜色")
        self.underline_color_button.clicked.connect(self.choose_underline_color)  # 连接下划线颜色选择事件
        
        underline_control_layout.addWidget(underline_width_label)
        underline_control_layout.addWidget(self.underline_width_spin)
        underline_control_layout.addWidget(underline_offset_label)
        underline_control_layout.addWidget(self.underline_offset_spin)
        underline_control_layout.addWidget(QLabel("颜色："))
        underline_control_layout.addWidget(self.underline_color_button)
        underline_control_layout.addStretch()
        
        layout.addWidget(self.underline_control)

        # 添加分隔线
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator2)

        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        # 添加字间距和行间距控制面板
        spacing_control = QWidget()
        spacing_layout = QHBoxLayout(spacing_control)
        spacing_layout.setContentsMargins(0, 0, 0, 0)
        
        # 字间距控制
        char_spacing_label = QLabel("字间距：")
        self.char_spacing_spin = QSpinBox()
        self.char_spacing_spin.setRange(0, 100)  # 字间距范围0-100像素
        self.char_spacing_spin.setValue(40)
        self.char_spacing_spin.setToolTip("调整字符之间的间距")
        
        # 行间距控制
        line_spacing_label = QLabel("行间距：")
        self.line_spacing_spin = QSpinBox()
        self.line_spacing_spin.setRange(0, 200)  # 行间距范围0-200像素
        self.line_spacing_spin.setValue(50)
        self.line_spacing_spin.setToolTip("调整行与行之间的间距")
        
        spacing_layout.addWidget(char_spacing_label)
        spacing_layout.addWidget(self.char_spacing_spin)
        spacing_layout.addWidget(line_spacing_label)
        spacing_layout.addWidget(self.line_spacing_spin)
        spacing_layout.addStretch()
        
        # 将间距控制面板添加到布局中
        layout.addWidget(spacing_control)

        # 连接信号
        self.char_spacing_spin.valueChanged.connect(self.on_spacing_changed)
        self.line_spacing_spin.valueChanged.connect(self.on_spacing_changed)

        # 椭圆控制面板的信号连接
        self.position_spin.valueChanged.connect(self.on_ellipse_param_changed)
        self.size_spin.valueChanged.connect(self.on_ellipse_param_changed)
        self.width_spin.valueChanged.connect(self.on_ellipse_param_changed)

        # 下划线控制面板的信号连接
        self.underline_width_spin.valueChanged.connect(self.on_underline_param_changed)
        self.underline_offset_spin.valueChanged.connect(self.on_underline_param_changed)

        # 连接样式按钮的点击事件
        self.underline_button.clicked.connect(lambda: self.add_style('underline'))
        self.circle_button.clicked.connect(lambda: self.add_style('circle'))
        self.ellipse_button.clicked.connect(lambda: self.add_style('ellipse'))
        self.clear_button.clicked.connect(self.clear_char_style)

    def keyPressEvent(self, event: QKeyEvent):
        """处理按键按下事件"""
        if event.key() == Qt.Key.Key_Shift:
            self.shift_pressed = True
        elif event.key() == Qt.Key.Key_Control:
            self.ctrl_pressed = True
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        """处理按键释放事件"""
        if event.key() == Qt.Key.Key_Shift:
            self.shift_pressed = False
        elif event.key() == Qt.Key.Key_Control:
            self.ctrl_pressed = False
        super().keyReleaseEvent(event)

    def on_text_changed(self):
        """当文本改变时"""
        # 重置样式标记
        self.text_marks = {}
        self.content_changed.emit()

    def on_char_selected(self, index):
        """当字符被选中时"""
        if self.shift_pressed and self.last_selected_index is not None:
            # Shift键按下时，选择范围
            start = min(self.last_selected_index, index)
            end = max(self.last_selected_index, index)
            self.selected_chars = set(range(start, end + 1))
        elif self.ctrl_pressed:
            # Ctrl键按下时，切换单个选择
            if index in self.selected_chars:
                self.selected_chars.remove(index)
            else:
                self.selected_chars.add(index)
        else:
            # 普通点击，清除之前的选择并选择当前字符
            self.selected_chars.clear()
            self.selected_chars.add(index)

        self.last_selected_index = index
        self.update_all_char_buttons()
        self.update_style_buttons()

    def update_style_buttons(self):
        """更新样式按钮和控制面板的状态"""
        has_selection = len(self.selected_chars) > 0
        self.underline_button.setEnabled(has_selection)
        self.circle_button.setEnabled(len(self.selected_chars) == 1)
        self.ellipse_button.setEnabled(has_selection)
        self.clear_button.setEnabled(has_selection)
        
        # 获取选中文字的样式
        selected_style = None
        selected_style_data = None
        for (start, end), style in self.text_marks.items():
            if any(i in range(start, end + 1) for i in self.selected_chars):
                selected_style = style['type']
                selected_style_data = style
                break

        # 更新控制面板的值
        if selected_style == 'ellipse' and selected_style_data:
            # 更新椭圆控制面板的值
            self.position_spin.setValue(selected_style_data.get('position', 0))
            self.size_spin.setValue(selected_style_data.get('size', 10))
            self.width_spin.setValue(selected_style_data.get('width', 2))
            self.current_color = selected_style_data.get('color', '#000000')
            self.color_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.current_color};
                    color: {'white' if QColor(self.current_color).lightness() < 128 else 'black'};
                    border: 1px solid #D9D9D9;
                    border-radius: 4px;
                    padding: 5px;
                }}
            """)
        elif selected_style == 'underline' and selected_style_data:
            # 更新下划线控制面板的值
            self.underline_width_spin.setValue(selected_style_data.get('width', 2))
            self.underline_offset_spin.setValue(selected_style_data.get('offset', 5))
            self.underline_current_color = selected_style_data.get('color', '#000000')
            self.underline_color_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.underline_current_color};
                    color: {'white' if QColor(self.underline_current_color).lightness() < 128 else 'black'};
                    border: 1px solid #D9D9D9;
                    border-radius: 4px;
                    padding: 5px;
                }}
            """)

    def add_style(self, style_type):
        """添加样式"""
        cursor = self.text_edit.textCursor()
        if not cursor.hasSelection():
            return

        start = cursor.selectionStart()
        end = cursor.selectionEnd() - 1
        
        if style_type == 'circle' and (end - start) > 0:
            return
            
        if style_type == 'ellipse' or style_type == 'underline':
            style_data = {
                'type': style_type,
                'width': (self.width_spin.value() if style_type == 'ellipse' 
                         else self.underline_width_spin.value()),
                'color': (self.current_color if style_type == 'ellipse' 
                         else self.underline_current_color)
            }
            
            if style_type == 'ellipse':
                style_data.update({
                    'position': self.position_spin.value(),
                    'size': self.size_spin.value(),
                })
            elif style_type == 'underline':
                style_data.update({
                    'offset': self.underline_offset_spin.value()
                })
            
            self.text_marks[(start, end)] = style_data
        else:
            self.text_marks[(start, start)] = {'type': style_type}

        self.content_changed.emit()
        self.style_applied.emit()

    def clear_char_style(self):
        """清除选中文字的样式"""
        cursor = self.text_edit.textCursor()
        if not cursor.hasSelection():
            return

        start = cursor.selectionStart()
        end = cursor.selectionEnd() - 1
        
        # 移除包含选中文字的样式
        marks_to_remove = []
        for (style_start, style_end), style in self.text_marks.items():
            if (start <= style_end and end >= style_start):
                marks_to_remove.append((style_start, style_end))
        
        for mark in marks_to_remove:
            del self.text_marks[mark]

        self.content_changed.emit()
        self.style_applied.emit()

    def update_all_char_buttons(self):
        """此方法已不再需要，保留为空方法以兼容现有代码"""
        pass

    def get_content(self):
        """获取内容和样式标记"""
        return {
            'text': self.text_edit.toPlainText(),
            'marks': self.text_marks,
            'font_size': self.font_size,
            'font_bold': self.font_bold,
            'char_spacing': self.char_spacing_spin.value(),
            'line_spacing': self.line_spacing_spin.value()
        }

    def set_content(self, content):
        """设置内容和样式标记"""
        self.text_edit.setPlainText(content.get('text', ''))
        self.text_marks = content.get('marks', {})
        self.font_size = content.get('font_size', 48)
        self.font_bold = content.get('font_bold', False)
        self.update_text_edit_font()
        self.update_all_char_buttons()

    def update_text_edit_font(self):
        """更新文本编辑器的字体 - 仅设置字体族，保持大小不变"""
        font = QFont("Microsoft YaHei UI", 14)  # 固定大小为14pt
        font.setBold(self.font_bold)
        self.text_edit.setFont(font)

    def on_font_size_changed(self, size):
        """当字号改变时"""
        self.font_size = size
        self.update_text_edit_font()
        self.update_all_char_buttons()
        self.font_changed.emit()
        self.style_applied.emit()

    def on_bold_changed(self, state):
        """当加粗状态改变时"""
        self.font_bold = bool(state)
        self.update_text_edit_font()
        self.update_all_char_buttons()
        self.font_changed.emit()
        self.style_applied.emit()

    def on_ellipse_param_changed(self):
        """当椭圆参数改变时"""
        cursor = self.text_edit.textCursor()
        if not cursor.hasSelection():
            return
        
        start = cursor.selectionStart()
        end = cursor.selectionEnd() - 1
        
        # 更新或创建椭圆样式
        style_key = None
        for (s, e) in self.text_marks.keys():
            if start <= e and end >= s:
                style_key = (s, e)
                break
        
        if style_key:
            # 更新现有样式
            self.text_marks[style_key].update({
                'position': self.position_spin.value(),
                'size': self.size_spin.value(),
                'width': self.width_spin.value(),
                'color': self.current_color
            })
        
        # 触发重新生成图片
        self.style_applied.emit()

    def on_spacing_changed(self):
        """当间距参数改变时"""
        self.style_applied.emit()

    def choose_color(self):
        """打开颜色选择对话框"""
        color = QColorDialog.getColor(initial=QColor(self.current_color))
        if color.isValid():
            self.current_color = color.name()
            # 更新按钮样式以显示当前颜色
            self.color_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.current_color};
                    color: {'white' if color.lightness() < 128 else 'black'};
                    border: 1px solid #D9D9D9;
                    border-radius: 4px;
                    padding: 5px;
                }}
            """)
            self.on_ellipse_param_changed()

    def choose_underline_color(self):
        """打开下划线颜色选择对话框"""
        color = QColorDialog.getColor(initial=QColor(self.underline_current_color))
        if color.isValid():
            self.underline_current_color = color.name()
            self.underline_color_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.underline_current_color};
                    color: {'white' if color.lightness() < 128 else 'black'};
                    border: 1px solid #D9D9D9;
                    border-radius: 4px;
                    padding: 5px;
                }}
            """)
            self.on_underline_param_changed()

    def on_underline_param_changed(self):
        """当下划线参数改变时"""
        cursor = self.text_edit.textCursor()
        if not cursor.hasSelection():
            return
        
        start = cursor.selectionStart()
        end = cursor.selectionEnd() - 1
        
        # 更新或创建下划线样式
        style_key = None
        for (s, e) in self.text_marks.keys():
            if start <= e and end >= s:
                style_key = (s, e)
                break
        
        if style_key:
            # 更新现有样式
            self.text_marks[style_key].update({
                'width': self.underline_width_spin.value(),
                'color': self.underline_current_color,
                'offset': self.underline_offset_spin.value()
            })
        
        # 触发重新生成图片
        self.style_applied.emit()

    def on_selection_changed(self):
        """当文本选择改变时"""
        cursor = self.text_edit.textCursor()
        has_selection = cursor.hasSelection()
        selection_length = len(cursor.selectedText())
        
        # 更新按钮状态
        self.underline_button.setEnabled(has_selection)
        self.circle_button.setEnabled(selection_length == 1)
        self.ellipse_button.setEnabled(has_selection)
        self.clear_button.setEnabled(has_selection)
        
        # 如果有选中的文字，检查是否已有样式
        if has_selection:
            start = cursor.selectionStart()
            end = cursor.selectionEnd() - 1
            
            # 查找选中文字的样式
            found_style = False
            for (style_start, style_end), style in self.text_marks.items():
                if (start <= style_end and end >= style_start):
                    found_style = True
                    # 更新控制面板的值
                    if style['type'] == 'ellipse':
                        # 启用椭圆控制面板
                        for widget in self.ellipse_control.findChildren((QSpinBox, QPushButton)):
                            widget.setEnabled(True)
                        # 禁用下划线控制面板
                        for widget in self.underline_control.findChildren((QSpinBox, QPushButton)):
                            widget.setEnabled(False)
                        
                        # 更新椭圆控制值
                        self.position_spin.setValue(style.get('position', 0))
                        self.size_spin.setValue(style.get('size', 10))
                        self.width_spin.setValue(style.get('width', 2))
                        self.current_color = style.get('color', '#000000')
                        self.update_color_button()
                        
                    elif style['type'] == 'underline':
                        # 启用下划线控制面板
                        for widget in self.underline_control.findChildren((QSpinBox, QPushButton)):
                            widget.setEnabled(True)
                        # 禁用椭圆控制面板
                        for widget in self.ellipse_control.findChildren((QSpinBox, QPushButton)):
                            widget.setEnabled(False)
                        
                        # 更新下划线控制值
                        self.underline_width_spin.setValue(style.get('width', 2))
                        self.underline_offset_spin.setValue(style.get('offset', 5))
                        self.underline_current_color = style.get('color', '#000000')
                        self.update_underline_color_button()
                    break
            
            if not found_style:
                # 如果选中的文字没有样式，启用所有控制面板
                for widget in self.ellipse_control.findChildren((QSpinBox, QPushButton)):
                    widget.setEnabled(True)
                for widget in self.underline_control.findChildren((QSpinBox, QPushButton)):
                    widget.setEnabled(True)
        else:
            # 如果没有选中文字，禁用所有控制面板
            for widget in self.ellipse_control.findChildren((QSpinBox, QPushButton)):
                widget.setEnabled(False)
            for widget in self.underline_control.findChildren((QSpinBox, QPushButton)):
                widget.setEnabled(False)

    def update_color_button(self):
        """更新椭圆颜色按钮样式"""
        self.color_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.current_color};
                color: {'white' if QColor(self.current_color).lightness() < 128 else 'black'};
                border: 1px solid #D9D9D9;
                border-radius: 4px;
                padding: 5px;
            }}
        """)

    def update_underline_color_button(self):
        """更新下划线颜色按钮样式"""
        self.underline_color_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.underline_current_color};
                color: {'white' if QColor(self.underline_current_color).lightness() < 128 else 'black'};
                border: 1px solid #D9D9D9;
                border-radius: 4px;
                padding: 5px;
            }}
        """)