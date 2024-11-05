from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QTabWidget, QTextEdit, QPushButton, QComboBox, 
                           QRadioButton, QLabel, QScrollArea, QFileDialog, 
                           QSizePolicy, QFrame)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QResizeEvent
from .text_editor import TextEditor
from .style_panel import StylePanel
from core.image_generator import ImageGenerator
from core.ai_helper import AIHelper
import asyncio
import os
import json
from datetime import datetime
from .styles import FusionStyle
from PIL import Image

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("小红书文字转图片工具")
        self.setMinimumSize(1200, 800)
        self.image_generator = ImageGenerator()
        self.current_images = []
        self.current_image_index = 0
        self.init_ui()
        # 初始化时显示默认背景
        self.preview_background()
        
    def init_ui(self):
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 创建标签页
        tabs = QTabWidget()
        
        # 手动录入标签页
        manual_tab = QWidget()
        manual_layout = QVBoxLayout(manual_tab)
        self.text_editor = TextEditor()
        manual_layout.addWidget(self.text_editor)
        manual_tab.setLayout(manual_layout)
        
        # 添加标签页（只添加手动录入）
        tabs.addTab(manual_tab, "文本编辑")
        
        # 样式面板
        self.style_panel = StylePanel()
        
        # 生成按钮
        self.generate_button = QPushButton("生成图片")
        
        # 添加所有组件到左侧布局
        left_layout.addWidget(tabs)
        left_layout.addWidget(self.style_panel)
        left_layout.addWidget(self.generate_button)
        
        # 右侧预览面板
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_content = QWidget()
        right_layout = QVBoxLayout(right_content)
        
        # 预览控制按钮
        preview_controls = QHBoxLayout()
        self.prev_button = QPushButton("上一页")
        self.next_button = QPushButton("下一页")
        self.page_label = QLabel("0/0")
        self.prev_button.clicked.connect(self.show_previous_image)
        self.next_button.clicked.connect(self.show_next_image)
        preview_controls.addWidget(self.prev_button)
        preview_controls.addWidget(self.page_label)
        preview_controls.addWidget(self.next_button)
        right_layout.addLayout(preview_controls)
        
        # 预览标签
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.preview_label)
        
        # 下载按钮
        self.download_button = QPushButton("下载所有图片")
        self.download_button.setEnabled(False)
        self.download_button.clicked.connect(self.download_images)
        right_layout.addWidget(self.download_button)
        
        right_scroll.setWidget(right_content)
        
        # 设置布局比例
        main_layout.addWidget(left_panel, 60)
        main_layout.addWidget(right_scroll, 40)
        
        # 设置右侧预览区域的最小和最大宽度
        right_scroll.setMinimumWidth(400)
        right_scroll.setMaximumWidth(600)
        
        # 优化预览标签的大小策略
        self.preview_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        
        # 设置滚动区域的框架样式
        right_scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        # 添加响应式布局支持
        self.right_content = right_content
        self.right_scroll = right_scroll
        
        # 连接信号
        self.generate_button.clicked.connect(self.generate_image)
        self.style_panel.style_changed.connect(self.preview_style_change)
        
        # 设置生成按钮为主要按钮样式
        self.generate_button.setObjectName("primaryButton")
        self.download_button.setObjectName("primaryButton")
    
    def generate_image(self):
        try:
            style = self.style_panel.get_current_style()
            content = self.text_editor.get_all_content()
            
            bg_value = style['background']
            bg_config = next((bg for bg in self.style_panel.config['backgrounds'] 
                            if bg['value'] == bg_value), None)
            bg_path = bg_config['url'] if bg_config else None
            
            # 生成多页图片
            self.current_images = self.image_generator.create_images(
                content,
                bg_path,
                style['font_style']
            )
            
            # 重置图片索引并显示第一页
            self.current_image_index = 0
            self.update_preview()
            
            # 更新页码显示
            self.page_label.setText(f"1/{len(self.current_images)}")
            
            # 更新导航按钮状态
            self.update_navigation_buttons()
            
            # 启用下载按钮
            self.download_button.setEnabled(True)
            
        except Exception as e:
            print(f"生成图片错误: {str(e)}")
            self.preview_label.setText("生成图片失败")
            self.download_button.setEnabled(False)
    
    def update_preview(self):
        """更新预览图片"""
        if not self.current_images or self.current_image_index >= len(self.current_images):
            return
            
        # 保存临时文件并显示
        temp_path = 'temp_preview.png'
        self.current_images[self.current_image_index].save(temp_path)
        
        # 显示预览
        pixmap = QPixmap(temp_path)
        scaled_pixmap = pixmap.scaled(
            self.preview_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.preview_label.setPixmap(scaled_pixmap)
        
        # 清理临时文件
        os.remove(temp_path)
    
    def show_previous_image(self):
        """显示上一页"""
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.update_preview()
            self.page_label.setText(f"{self.current_image_index + 1}/{len(self.current_images)}")
            self.update_navigation_buttons()
    
    def show_next_image(self):
        """显示下一页"""
        if self.current_image_index < len(self.current_images) - 1:
            self.current_image_index += 1
            self.update_preview()
            self.page_label.setText(f"{self.current_image_index + 1}/{len(self.current_images)}")
            self.update_navigation_buttons()
    
    def update_navigation_buttons(self):
        """更新导航按钮状态"""
        self.prev_button.setEnabled(self.current_image_index > 0)
        self.next_button.setEnabled(self.current_image_index < len(self.current_images) - 1)
    
    def download_images(self):
        """下载所有图片"""
        if not self.current_images:
            return
            
        try:
            # 选择保存目录
            directory = QFileDialog.getExistingDirectory(
                self,
                "选择保存目录",
                "",
                QFileDialog.Option.ShowDirsOnly
            )
            
            if directory:
                # 生成时间戳
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                
                # 保存所有图片
                for i, image in enumerate(self.current_images):
                    filename = f"小红书图片_{timestamp}_第{i+1}页.png"
                    filepath = os.path.join(directory, filename)
                    image.save(filepath, 'PNG')
                
        except Exception as e:
            print(f"保存图片错误: {str(e)}")
    
    def preview_style_change(self, style):
        """当样式改变时更新预览"""
        if self.current_images:
            # 如果已经生成了图片，则重新生成
            self.generate_image()
        else:
            # 如果还没有生成图片，只预览背景
            self.preview_background()
    
    def resizeEvent(self, event: QResizeEvent) -> None:
        """处理窗口大小变化事件"""
        super().resizeEvent(event)
        self.update_preview_size()
        
    def update_preview_size(self):
        """更新预览图片大小"""
        # 获取滚动区域的可见大小
        available_width = min(self.right_scroll.width() - 40, 560)  # 限制最大宽度
        available_height = self.right_scroll.height() - 100  # 留出按钮和控件的空间
        
        # 计算保持宽高比的最大尺寸
        image_ratio = 3/4  # 图片的宽高比
        if available_width * image_ratio <= available_height:
            # 以宽度为基准
            preview_width = available_width
            preview_height = available_width * image_ratio
        else:
            # 以高度为基准
            preview_height = available_height
            preview_width = available_height / image_ratio
        
        # 更新预览标签的固定大小
        self.preview_label.setFixedSize(QSize(int(preview_width), int(preview_height)))
        
        # 更新当前显示的图片或背景
        if self.current_images:
            self.update_preview()
        else:
            self.preview_background()
    
    def preview_background(self):
        """预览当前选择的背景"""
        try:
            # 获取当前选择的背景
            style = self.style_panel.get_current_style()
            bg_value = style['background']
            bg_config = next((bg for bg in self.style_panel.config['backgrounds'] 
                            if bg['value'] == bg_value), None)
            
            if bg_config and bg_config['url']:
                # 创建一个空白图片
                image = Image.new('RGB', (self.image_generator.width, self.image_generator.height), 'white')
                
                # 加载并粘贴背景
                try:
                    bg = Image.open(bg_config['url'])
                    bg = bg.resize((self.image_generator.width, self.image_generator.height))
                    image.paste(bg, (0, 0))
                    
                    # 保存临时文件并显示
                    temp_path = 'temp_preview.png'
                    image.save(temp_path)
                    
                    # 显示预览
                    pixmap = QPixmap(temp_path)
                    scaled_pixmap = pixmap.scaled(
                        self.preview_label.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.preview_label.setPixmap(scaled_pixmap)
                    
                    # 清理临时文件
                    os.remove(temp_path)
                except Exception as e:
                    print(f"背景图片加载失败: {str(e)}")
                    self.preview_label.setText("背景预览失败")
            else:
                # 如果没有背景配置，显示空白
                self.preview_label.setText("无背景预览")
                
        except Exception as e:
            print(f"背景预览错误: {str(e)}")
            self.preview_label.setText("预览失败")