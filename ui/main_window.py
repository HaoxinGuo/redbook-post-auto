from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QTabWidget, QTextEdit, QPushButton, QComboBox, 
                           QRadioButton, QLabel, QScrollArea, QFileDialog, 
                           QSizePolicy, QFrame)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QResizeEvent, QIcon
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
        self.setMinimumSize(1400, 800)
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
        
        # 创建按钮容器
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        
        # 生成按钮
        self.generate_button = QPushButton("生成图片")
        self.generate_button.setObjectName("primaryButton")
        
        # 下载按钮
        self.download_button = QPushButton("下载所有图片")
        self.download_button.setEnabled(False)
        self.download_button.setObjectName("primaryButton")
        self.download_button.clicked.connect(self.download_images)
        
        # 添加按钮到局
        button_layout.addWidget(self.generate_button)
        button_layout.addWidget(self.download_button)
        
        left_layout.addWidget(tabs)
        left_layout.addWidget(self.style_panel)
        left_layout.addWidget(button_container)  # 添加按钮容器
        
        # 右侧预览面板
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_content = QWidget()
        right_layout = QVBoxLayout(right_content)
        right_layout.setSpacing(0)  # 将垂直间距设为0
        right_layout.setContentsMargins(0, 0, 0, 0)  # 移除所有边距
        
        # 创建一个水平布局的容器来包含预览图片和导航按钮
        preview_container = QWidget()
        preview_container_layout = QHBoxLayout(preview_container)
        preview_container_layout.setSpacing(10)  # 设置按钮和预览图片之间的间距
        preview_container_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建并设置导航按钮
        self.prev_button = QPushButton()
        self.prev_button.setFixedSize(40, 40)  # 调整按钮大小为正方形
        self.prev_button.setIcon(QIcon("resources/icons/left-arrow.png"))  # 设置左箭头图标
        self.prev_button.setIconSize(QSize(24, 24))  # 设置图标大小
        self.prev_button.clicked.connect(self.show_previous_image)
        self.prev_button.setEnabled(False)  # 初始状态禁用
        self.prev_button.setToolTip("上一页")  # 添加悬停提示
        
        self.next_button = QPushButton()
        self.next_button.setFixedSize(40, 40)  # 调整按钮大小为正方形
        self.next_button.setIcon(QIcon("resources/icons/right-arrow.png"))  # 设置右箭头图标
        self.next_button.setIconSize(QSize(24, 24))  # 设置图标大小
        self.next_button.clicked.connect(self.show_next_image)
        self.next_button.setEnabled(False)  # 初始状态禁用
        self.next_button.setToolTip("下一页")  # 添加悬停提示
        
        # 预览标签
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 将组件添加到水平布局中
        preview_container_layout.addWidget(self.prev_button)
        preview_container_layout.addWidget(self.preview_label, 1)  # 预览图片占据更多空间
        preview_container_layout.addWidget(self.next_button)
        
        # 将预览容器添加到主布局
        right_layout.addWidget(preview_container, 1)  # 添加拉伸因子使其填充可用空间
        
        right_scroll.setWidget(right_content)
        
        # 设置布局比例
        main_layout.addWidget(left_panel, 60)
        main_layout.addWidget(right_scroll, 40)
        
        # 设置右侧预览区域的宽度范围
        right_scroll.setMinimumWidth(800)
        right_scroll.setMaximumWidth(1200)
        
        # 添加响应式布局支持
        self.right_content = right_content
        self.right_scroll = right_scroll
        
        # 连接信号
        self.generate_button.clicked.connect(self.generate_image)
        self.style_panel.style_changed.connect(self.preview_style_change)
        
        # 设置按钮样式
        self.generate_button.setObjectName("primaryButton")
        self.download_button.setObjectName("primaryButton")
        
        # 可以添加样式来美化按钮
        button_style = """
            QPushButton {
                border: 1px solid #D9D9D9;
                border-radius: 20px;
                background-color: white;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #F5F5F5;
                border-color: #4096FF;
            }
            QPushButton:pressed {
                background-color: #E6E6E6;
            }
            QPushButton:disabled {
                background-color: #F5F5F5;
                border-color: #D9D9D9;
            }
        """
        self.prev_button.setStyleSheet(button_style)
        self.next_button.setStyleSheet(button_style)
    
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
            
            # 更新导航按钮状态
            self.update_navigation_buttons()
            
            # 启用下载按钮
            self.download_button.setEnabled(True)
            
            print(f"生成了 {len(self.current_images)} 张图片")
            
        except Exception as e:
            print(f"生成图片错误: {str(e)}")  # 打印具体错误信息
            self.preview_label.setText("生成图片失败")
            self.download_button.setEnabled(False)
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
    
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
            self.update_navigation_buttons()
    
    def show_next_image(self):
        """显示下一页"""
        if self.current_image_index < len(self.current_images) - 1:
            self.current_image_index += 1
            self.update_preview()
            self.update_navigation_buttons()
    
    def update_navigation_buttons(self):
        """更新导航按钮状态"""
        self.prev_button.setEnabled(self.current_image_index > 0)
        self.next_button.setEnabled(self.current_image_index < len(self.current_images) - 1)
    
    def download_images(self):
        """下载所有图片"""
        if not self.current_images:
            print("没有可下载的图片")
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
                    filename = f"小红书图片_{timestamp}_第{i + 1}页.png"
                    filepath = os.path.join(directory, filename)
                    
                    # 保存图片
                    image.save(filepath, 'PNG')
                    
                print(f"所有图片已保存到: {directory}")
            else:
                print("未选择保存目录")
                
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
        # 获取预览容器的可见大小
        available_width = min(self.right_scroll.width() - 10, 1000)  # 减少边距
        available_height = self.right_scroll.height() - 50  # 为控制按钮预留空间
        
        # 计算保持宽高比的最大尺寸
        image_ratio = 3/4  # 图片的宽高比
        if available_width * image_ratio <= available_height:
            preview_width = available_width
            preview_height = available_width * image_ratio
        else:
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