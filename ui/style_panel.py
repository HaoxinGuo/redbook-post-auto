from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QComboBox, QRadioButton, QColorDialog, QPushButton)
from PyQt6.QtCore import pyqtSignal
import json
import os

class StylePanel(QWidget):
    style_changed = pyqtSignal(dict)  # 样式变化信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = self.load_config()
        self.init_ui()

    def load_config(self):
        """加载配置文件"""
        config_path = os.path.join('resources', 'config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return {
                "backgrounds": [],
                "fonts": {
                    "normal": "",
                    "handwritten": ""
                }
            }

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 背景选择
        bg_group = QWidget()
        bg_layout = QVBoxLayout(bg_group)
        
        bg_label = QLabel("选择背景：")
        self.bg_combo = QComboBox()
        # 从配置文件加载背景选项
        for bg in self.config.get('backgrounds', []):
            self.bg_combo.addItem(bg['name'], bg['value'])
        
        bg_layout.addWidget(bg_label)
        bg_layout.addWidget(self.bg_combo)
        
        # 字体样式
        font_group = QWidget()
        font_layout = QVBoxLayout(font_group)
        
        font_label = QLabel("字体样式：")
        font_buttons = QHBoxLayout()
        
        self.normal_font = QRadioButton("正常")
        self.handwritten_font = QRadioButton("手写")
        self.normal_font.setChecked(True)
        
        font_buttons.addWidget(self.normal_font)
        font_buttons.addWidget(self.handwritten_font)
        
        font_layout.addWidget(font_label)
        font_layout.addLayout(font_buttons)
        
        # 文字颜色
        color_group = QWidget()
        color_layout = QVBoxLayout(color_group)
        
        text_color_label = QLabel("文字颜色：")
        self.text_color_button = QPushButton("选择颜色")
        self.text_color_button.clicked.connect(self.choose_text_color)
        
        color_layout.addWidget(text_color_label)
        color_layout.addWidget(self.text_color_button)
        
        # 添加所有组件到主布局
        layout.addWidget(bg_group)
        layout.addWidget(font_group)
        layout.addWidget(color_group)
        layout.addStretch()
        
        # 连接信号
        self.bg_combo.currentIndexChanged.connect(self.emit_style_change)
        self.normal_font.toggled.connect(self.emit_style_change)
        self.handwritten_font.toggled.connect(self.emit_style_change)

    def choose_text_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.text_color_button.setStyleSheet(
                f"background-color: {color.name()}"
            )
            self.emit_style_change()

    def get_current_style(self):
        """获取当前样式设置"""
        return {
            'background': self.bg_combo.currentData(),
            'font_style': 'handwritten' if self.handwritten_font.isChecked() else 'normal',
            'text_color': self.text_color_button.palette().button().color().name()
        }

    def emit_style_change(self):
        """发出样式变化信号"""
        self.style_changed.emit(self.get_current_style())

    def set_style(self, style_dict):
        """设置样式"""
        # 设置背景
        index = self.bg_combo.findData(style_dict.get('background'))
        if index >= 0:
            self.bg_combo.setCurrentIndex(index)
            
        # 设置字体样式
        if style_dict.get('font_style') == 'handwritten':
            self.handwritten_font.setChecked(True)
        else:
            self.normal_font.setChecked(True)
            
        # 设置文字颜色
        if 'text_color' in style_dict:
            self.text_color_button.setStyleSheet(
                f"background-color: {style_dict['text_color']}"
            )