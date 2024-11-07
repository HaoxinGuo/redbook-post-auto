from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QTabWidget, QTextEdit, QPushButton, QComboBox, 
                           QRadioButton, QLabel, QScrollArea, QFileDialog, 
                           QSizePolicy, QFrame)
from PyQt6.QtCore import Qt, QSize, QPoint
from PyQt6.QtGui import QPixmap, QResizeEvent, QIcon, QPainter, QPen, QColor
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
from PyQt6.QtCore import QTimer
from .style_text_editor import StyleTextEditor
from PIL import ImageDraw
from PIL import ImageFont
from ui.styles import *  # 或者具体的样式导入

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("小红书文字转图片工具")
        self.setMinimumSize(1400, 800)
        self.image_generator = ImageGenerator()
        self.current_images = []
        self.current_image_index = 0
        self.init_ui()
        
        # 在显示窗口之先计算一次预览尺寸
        self.calculate_initial_preview_size()
        
        # 初始化时显示默认背景
        self.preview_background()
        
        # 应用样式到具体的控件
        #self.setStyleSheet(your_style_definition)  # your_style_definition 来自 styles.py
        
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
        self.tabs = QTabWidget()
        
        # 手动录入标签页
        manual_tab = QWidget()
        manual_layout = QVBoxLayout(manual_tab)
        self.text_editor = TextEditor()
        manual_layout.addWidget(self.text_editor)
        manual_tab.setLayout(manual_layout)
        
        # 添加标签页（只添加手动录入）
        self.tabs.addTab(manual_tab, "文本编辑")
        
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
        
        left_layout.addWidget(self.tabs)
        left_layout.addWidget(self.style_panel)
        left_layout.addWidget(button_container)  # 添加按钮容器
        
        # 样式文本编辑标签页
        self.style_text_tab = QWidget()
        style_text_layout = QVBoxLayout(self.style_text_tab)
        self.style_text_editor = StyleTextEditor()
        style_text_layout.addWidget(self.style_text_editor)
        self.style_text_tab.setLayout(style_text_layout)
        
        # 添加样式文本编辑标签页
        self.tabs.addTab(self.style_text_tab, "封面编辑")
        
        # 右侧预览面板
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)  # 改为垂直布局
        right_layout.setSpacing(0)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建预览内容容器
        preview_content = QWidget()
        preview_content_layout = QVBoxLayout(preview_content)
        preview_content_layout.setContentsMargins(20, 20, 20, 20)
        preview_content_layout.setSpacing(10)
        
        # 创建图片预览区域容器（用于水平居中）
        preview_container = QWidget()
        preview_container_layout = QHBoxLayout(preview_container)
        preview_container_layout.setContentsMargins(0, 0, 0, 0)
        preview_container_layout.setSpacing(0)
        
        # 添加左侧弹性空间
        preview_container_layout.addStretch(1)
        
        # 创建图片预览标签
        self.preview_label = PreviewLabel()
        self.preview_label.style_text_editor = self.style_text_editor
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setSizePolicy(
            QSizePolicy.Policy.Fixed,  # 改为固定宽度
            QSizePolicy.Policy.Fixed   # 改为固定高度
        )
        
        # 设置初始最小尺寸
        initial_width = 400
        initial_height = int(initial_width * 4/3)
        self.preview_label.setMinimumSize(initial_width, initial_height)
        
        # 将预览标签添加到容器
        preview_container_layout.addWidget(self.preview_label)
        
        # 添加右侧弹性空间
        preview_container_layout.addStretch(1)
        
        # 添加顶部弹性空间
        preview_content_layout.addStretch(1)
        
        # 添加预览容器
        preview_content_layout.addWidget(preview_container)
        
        # 添加底部弹性空间
        preview_content_layout.addStretch(1)
        
        # 创建导航按钮容器
        nav_container = QWidget()
        nav_layout = QHBoxLayout(nav_container)  # 水平布局
        nav_layout.setContentsMargins(0, 0, 0, 0)  # 移除内边距
        
        # 创建并设置导航按钮
        self.prev_button = QPushButton("上一页")
        self.prev_button.setFixedSize(100, 40)
        self.prev_button.clicked.connect(self.show_previous_image)
        self.prev_button.setEnabled(False)
        
        self.next_button = QPushButton("下一页")
        self.next_button.setFixedSize(100, 40)
        self.next_button.clicked.connect(self.show_next_image)
        self.next_button.setEnabled(False)
        
        # 使用两个弹性空间来实现按钮的左右对齐
        nav_layout.addWidget(self.prev_button)
        nav_layout.addStretch(1)  # 添加弹性空间
        nav_layout.addWidget(self.next_button)
        
        # 将预览标签和导航按钮添加到预览内容布局
        preview_content_layout.addWidget(nav_container)
        
        # 创建滚动区域
        self.right_scroll = QScrollArea()
        self.right_scroll.setWidget(preview_content)
        self.right_scroll.setWidgetResizable(True)
        self.right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.right_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.right_scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 将滚动区域添加到右侧面板布局
        right_layout.addWidget(self.right_scroll)
        
        # 设置右侧预览区域的宽度范围
        right_panel.setMinimumWidth(600)
        right_panel.setMaximumWidth(1200)
        
        # 设置按钮样式
        button_style = """
            QPushButton {
                border: 1px solid #D9D9D9;
                border-radius: 4px;
                background-color: white;
                padding: 8px 16px;
                font-size: 14px;
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
                color: #00000040;
            }
        """
        self.prev_button.setStyleSheet(button_style)
        self.next_button.setStyleSheet(button_style)
        
        # 设置布局比例
        main_layout.addWidget(left_panel, 70)
        main_layout.addWidget(right_panel, 30)
        
        # 连接信号
        self.generate_button.clicked.connect(self.generate_image)
        self.style_panel.style_changed.connect(self.preview_style_change)
        self.style_text_editor.content_changed.connect(self.on_style_text_changed)
        
        # 接样式应用信号生成图片方法
        self.style_text_editor.style_applied.connect(self.generate_image)
        
        # 设置按钮
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
            bg_value = style['background']
            bg_config = next((bg for bg in self.style_panel.config['backgrounds'] 
                            if bg['value'] == bg_value), None)
            bg_path = bg_config['url'] if bg_config else None

            # 获取当前激活的标签页
            current_tab = self.tabs.currentWidget()
            
            if current_tab == self.style_text_tab:
                # 处理封面编辑的内容
                content = self.style_text_editor.get_content()
                # 创建单页图片
                image = Image.new('RGB', (self.image_generator.width, self.image_generator.height), 'white')
                
                # 加载背景
                if bg_path:
                    try:
                        bg = Image.open(bg_path)
                        bg = bg.resize((self.image_generator.width, self.image_generator.height))
                        image.paste(bg, (0, 0))
                    except Exception as e:
                        print(f"加载背景图片失败: {str(e)}")
                
                # 创建绘图对象
                draw = ImageDraw.Draw(image)
                
                # 设置字体
                font_size = content.get('font_size', 48)  # 使用用户设置的字号
                font_path = os.path.join('resources', 'fonts', 'SourceHanSansSC-VF.ttf')
                if content.get('font_bold'):
                    # 如果需要加粗，使用粗体字体文件
                    font_path = os.path.join('resources', 'fonts', 'SourceHanSansHWSC-Bold.otf')  # 使用已有的粗体字体
                
                try:
                    font = ImageFont.truetype(font_path, font_size)
                except Exception as e:
                    print(f"加载字体失败: {str(e)}")
                    return
                
                # 计算文本位置（居中）
                text = content['text']
                text_width = font.getlength(text)
                x = (self.image_generator.width - text_width) // 2
                y = (self.image_generator.height - font_size) // 2
                
                # 使用 draw_styled_text 绘制带样式的文本
                self.image_generator.draw_styled_text(
                    draw, 
                    text, 
                    content['marks'],
                    x, 
                    y, 
                    font,
                    char_spacing=content.get('char_spacing', 0),
                    line_spacing=content.get('line_spacing', 20)
                )
                
                self.current_images = [image]
                
                # 更新预览标签中的椭圆标记
                self.preview_label.update_ellipse_marks(content['marks'])
            
            else:
                # 处理普通文本编辑的内容
                content = self.text_editor.get_all_content()
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
            print(f"生成图片错误: {str(e)}")
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
        
        # 加载图片
        pixmap = QPixmap(temp_path)
        
        # 获取预览标签的大小
        label_size = self.preview_label.size()
        
        # 缩放图片以填充预览标签，保持宽高比
        scaled_pixmap = pixmap.scaled(
            label_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # 显示图片
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
            # 获取当前标签页
            current_tab = self.tabs.currentWidget()
            
            # 选择保存目录
            directory = QFileDialog.getExistingDirectory(
                self,
                "选择保存目录",
                "",
                QFileDialog.Option.ShowDirsOnly
            )
            
            if directory:
                if current_tab == self.style_text_tab:
                    # 封面编辑模式：直接保存图片
                    content = self.style_text_editor.text_edit.toPlainText()
                    # 去除可能存在的非法文件名字符
                    safe_content = "".join(c for c in content if c not in r'\/:*?"<>|')
                    filename = f"{safe_content}_封面.png"
                    filepath = os.path.join(directory, filename)
                    
                    # 保存图片
                    self.current_images[0].save(filepath, 'PNG')
                    print(f"封面图片已保存: {filepath}")
                    
                else:
                    # 文本编辑模式：创建日期-标题文件夹
                    content = self.text_editor.get_all_content()
                    title = ""
                    
                    # 查找第一个标题块
                    for item in content:
                        if item['type'] == 'title' and item.get('text', '').strip():
                            title = item['text'].strip()
                            break
                    
                    if not title:
                        title = "未命名"
                    
                    # 去除可能存在的非法文件名字符
                    safe_title = "".join(c for c in title if c not in r'\/:*?"<>|')
                    
                    # 创建文件夹名称：日期-标题
                    today = datetime.now().strftime('%Y%m%d')
                    folder_name = f"{today}-{safe_title}"
                    folder_path = os.path.join(directory, folder_name)
                    
                    # 创建文件夹
                    os.makedirs(folder_path, exist_ok=True)
                    
                    # 保存所有图片
                    for i, image in enumerate(self.current_images):
                        filename = f"{safe_title}_{i + 1}.png"
                        filepath = os.path.join(folder_path, filename)
                        
                        # 保存图片
                        image.save(filepath, 'PNG')
                    
                    print(f"所有图片已保存到文件夹: {folder_path}")
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
        
    def calculate_initial_preview_size(self):
        """计算初始预览尺寸"""
        # 获取右侧面板的初始尺寸
        right_width = int(self.width() * 0.4)  # 右侧面板占40%
        right_height = self.height()
        
        # 计算可用空间，考虑边距和导航按钮
        available_width = right_width - 100  # 减去导航按钮宽度和边距
        available_height = right_height - 40  # 减去上下边距
        
        # 确保可用尺寸不小于最小值
        available_width = max(400, available_width)
        available_height = max(533, available_height)
        
        # 计算保持宽高比的最大尺寸
        image_ratio = 3/4  # 图片的宽高比
        container_ratio = available_width / available_height
        
        if container_ratio > image_ratio:
            # 如果容器更宽，以高度为基准
            preview_height = available_height
            preview_width = preview_height / image_ratio
        else:
            # 如果容器更高，以宽度为基准
            preview_width = available_width
            preview_height = preview_width * image_ratio
        
        # 更新预览标签的固定大小
        self.preview_label.setFixedSize(QSize(int(preview_width), int(preview_height)))
    
    def update_preview_size(self):
        """更新预览图片大小"""
        # 获取滚动区域的可见大小
        viewport_width = self.right_scroll.viewport().width()
        viewport_height = self.right_scroll.viewport().height()
        
        # 计算可用空间，考虑边距和导航按钮
        available_width = viewport_width - 40  # 减去左右边距
        available_height = viewport_height - 40  # 减去上下边距
        
        # 确保可用尺寸不小于最小值
        available_width = max(400, available_width)
        available_height = max(533, available_height)
        
        # 计算持宽高比的最大尺寸
        image_ratio = 3/4  # 图片的宽高比
        
        # 计算基于宽度和高度的可能尺寸
        width_based_height = available_width * image_ratio
        height_based_width = available_height / image_ratio
        
        # 选择较小的尺寸以确保完全可见
        if width_based_height <= available_height:
            # 以宽度为基准
            preview_width = available_width
            preview_height = width_based_height
        else:
            # 以高度为基准
            preview_width = height_based_width
            preview_height = available_height
        
        # 确保尺寸不超过可见区域
        preview_width = min(preview_width, available_width)
        preview_height = min(preview_height, available_height)
        
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
                # 加背景图片
                pixmap = QPixmap(bg_config['url'])
                
                # 获取预览标签的大小
                label_size = self.preview_label.size()
                
                # 缩放图片以填充预览标签，保持宽高比
                scaled_pixmap = pixmap.scaled(
                    label_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                # 显示预览
                self.preview_label.setPixmap(scaled_pixmap)
            else:
                # 如果没有背景配置，显示空白
                self.preview_label.clear()
                
        except Exception as e:
            print(f"背景预览错误: {str(e)}")
            self.preview_label.clear()
    
    def on_style_text_changed(self):
        """当样式文本编辑器的内容改变时"""
        # 移除自动生成图片的逻辑，只在点击生成按钮时生成
        pass

class PreviewLabel(QLabel):
    """自定义预览标签，支持椭圆调整"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.dragging = False
        self.resizing = False
        self.adjusting_width = False
        self.drag_start = QPoint()
        self.current_ellipse = None
        self.current_underline = None
        self.ellipse_marks = []
        self.underline_marks = []
        self.style_text_editor = None
        self.scale_factor = 1.0

    def update_scale_factor(self):
        """更新缩放比例"""
        if not self.pixmap():
            return
        # 计算预览图片相对于原始图片的缩放比例
        self.scale_factor = self.pixmap().width() / 1080  # 1080是原始图片宽度

    def setPixmap(self, pixmap):
        """重写setPixmap方法以更新缩放比例"""
        super().setPixmap(pixmap)
        self.update_scale_factor()

    def get_real_coordinates(self, pos):
        """将预览坐标转换为实际图片坐标"""
        if not self.pixmap():
            return pos
        # 获取图片在标签中的实际位置
        x_offset = (self.width() - self.pixmap().width()) // 2
        y_offset = (self.height() - self.pixmap().height()) // 2
        # 转换坐标
        real_x = (pos.x() - x_offset) / self.scale_factor
        real_y = (pos.y() - y_offset) / self.scale_factor
        return QPoint(int(real_x), int(real_y))

    def get_preview_coordinates(self, real_pos):
        """将实际图片坐标转换为预览坐标"""
        if not self.pixmap():
            return real_pos
        x_offset = (self.width() - self.pixmap().width()) // 2
        y_offset = (self.height() - self.pixmap().height()) // 2
        preview_x = real_pos.x() * self.scale_factor + x_offset
        preview_y = real_pos.y() * self.scale_factor + y_offset
        return QPoint(int(preview_x), int(preview_y))

    def is_on_ellipse_edge(self, pos, ellipse):
        """检查点是否在椭圆边缘"""
        real_pos = self.get_real_coordinates(pos)
        
        # 算椭圆的边界框
        char_width = 32 * self.scale_factor  # 考虑缩放因子
        text_x = (self.width() - len(self.style_text_editor.text_edit.toPlainText()) * char_width) // 2
        x1 = text_x + ellipse['start'] * char_width - ellipse['size'] * self.scale_factor
        x2 = text_x + (ellipse['end'] + 1) * char_width + ellipse['size'] * self.scale_factor
        y1 = self.height() // 2 - 24 * self.scale_factor - ellipse['size'] * self.scale_factor + ellipse['position'] * self.scale_factor
        y2 = self.height() // 2 + 24 * self.scale_factor + ellipse['size'] * self.scale_factor + ellipse['position'] * self.scale_factor
        
        # 检查是否在边缘区域（边缘区域定义为距离边框5像素以内）
        edge_threshold = 5 * self.scale_factor
        x, y = pos.x(), pos.y()
        
        # 简化的椭圆边缘检测
        if (abs(x - x1) <= edge_threshold or abs(x - x2) <= edge_threshold) and y1 <= y <= y2:
            return True
        if (abs(y - y1) <= edge_threshold or abs(y - y2) <= edge_threshold) and x1 <= x <= x2:
            return True
        return False

    def is_on_ellipse_border(self, pos, ellipse):
        """检查点是否在椭圆边框上"""
        real_pos = self.get_real_coordinates(pos)
        
        # 计算椭圆的边界框
        char_width = 32 * self.scale_factor
        text_x = (self.width() - len(self.style_text_editor.text_edit.toPlainText()) * char_width) // 2
        x1 = text_x + ellipse['start'] * char_width - ellipse['size'] * self.scale_factor
        x2 = text_x + (ellipse['end'] + 1) * char_width + ellipse['size'] * self.scale_factor
        y1 = self.height() // 2 - 24 * self.scale_factor - ellipse['size'] * self.scale_factor + ellipse['position'] * self.scale_factor
        y2 = self.height() // 2 + 24 * self.scale_factor + ellipse['size'] * self.scale_factor + ellipse['position'] * self.scale_factor
        
        # 检查是否在边框上（边框区域定义为距离边框2像素以内）
        border_threshold = 2 * self.scale_factor
        x, y = pos.x(), pos.y()
        
        # 简化的边框检测
        if (abs(x - x1) <= border_threshold or abs(x - x2) <= border_threshold) and y1 <= y <= y2:
            return True
        if (abs(y - y1) <= border_threshold or abs(y - y2) <= border_threshold) and x1 <= x <= x2:
            return True
        return False

    def is_inside_ellipse(self, pos, ellipse):
        """检查点是否在椭圆内部"""
        real_pos = self.get_real_coordinates(pos)
        
        # 计算椭圆的边界框
        char_width = 32 * self.scale_factor
        text_x = (self.width() - len(self.style_text_editor.text_edit.toPlainText()) * char_width) // 2
        x1 = text_x + ellipse['start'] * char_width - ellipse['size'] * self.scale_factor
        x2 = text_x + (ellipse['end'] + 1) * char_width + ellipse['size'] * self.scale_factor
        y1 = self.height() // 2 - 24 * self.scale_factor - ellipse['size'] * self.scale_factor + ellipse['position'] * self.scale_factor
        y2 = self.height() // 2 + 24 * self.scale_factor + ellipse['size'] * self.scale_factor + ellipse['position'] * self.scale_factor
        
        # 检查是否在圆内部
        x, y = pos.x(), pos.y()
        return x1 <= x <= x2 and y1 <= y <= y2

    def is_on_underline(self, pos, underline):
        """检查点是否在下划线上"""
        real_pos = self.get_real_coordinates(pos)
        
        # 计算下划线的位置
        char_width = 32 * self.scale_factor
        text_x = (self.width() - len(self.style_text_editor.text_edit.toPlainText()) * char_width) // 2
        x1 = text_x + underline['start'] * char_width
        x2 = text_x + (underline['end'] + 1) * char_width
        y = self.height() // 2 + 24 * self.scale_factor + underline['offset'] * self.scale_factor
        
        # 检查是否在下划线区域内（考虑线条宽度）
        threshold = max(5, underline['width']) * self.scale_factor
        x, pos_y = pos.x(), pos.y()
        return x1 <= x <= x2 and abs(y - pos_y) <= threshold

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # 先检查椭圆
            for ellipse in self.ellipse_marks:
                if self.is_on_ellipse_edge(event.pos(), ellipse):
                    self.resizing = True
                    self.current_ellipse = ellipse
                    self.current_underline = None
                    self.drag_start = event.pos()
                    self.select_text_range(ellipse['start'], ellipse['end'])
                    return
                elif self.is_on_ellipse_border(event.pos(), ellipse):
                    self.adjusting_width = True
                    self.current_ellipse = ellipse
                    self.current_underline = None
                    self.drag_start = event.pos()
                    self.select_text_range(ellipse['start'], ellipse['end'])
                    return
                elif self.is_inside_ellipse(event.pos(), ellipse):
                    self.dragging = True
                    self.current_ellipse = ellipse
                    self.current_underline = None
                    self.drag_start = event.pos()
                    self.select_text_range(ellipse['start'], ellipse['end'])
                    return

            # 再检查下划线
            for underline in self.underline_marks:
                if self.is_on_underline(event.pos(), underline):
                    self.current_underline = underline
                    self.current_ellipse = None
                    self.drag_start = event.pos()
                    self.select_text_range(underline['start'], underline['end'])
                    return

    def select_text_range(self, start, end):
        """在文本编辑器中选中指定范围的文本"""
        if self.style_text_editor:
            cursor = self.style_text_editor.text_edit.textCursor()
            cursor.setPosition(start)
            cursor.setPosition(end + 1, QTextCursor.MoveMode.KeepAnchor)
            self.style_text_editor.text_edit.setTextCursor(cursor)

    def mouseMoveEvent(self, event):
        if self.dragging and self.current_ellipse:
            # 移动椭圆
            current_pos = self.get_real_coordinates(event.pos())
            start_pos = self.get_real_coordinates(self.drag_start)
            delta = current_pos.y() - start_pos.y()
            self.current_ellipse['position'] = max(-20, min(20, 
                self.current_ellipse['position'] + int(delta / self.scale_factor)))
            self.drag_start = event.pos()
            self.update_style_editor()
        elif self.resizing and self.current_ellipse:
            # 调整椭圆大小
            current_pos = self.get_real_coordinates(event.pos())
            start_pos = self.get_real_coordinates(self.drag_start)
            delta = current_pos.x() - start_pos.x()
            self.current_ellipse['size'] = max(5, min(30, 
                self.current_ellipse['size'] + int(delta / self.scale_factor)))
            self.drag_start = event.pos()
            self.update_style_editor()
        elif self.adjusting_width and self.current_ellipse:
            # 调整线条粗细
            current_pos = self.get_real_coordinates(event.pos())
            start_pos = self.get_real_coordinates(self.drag_start)
            delta = current_pos.y() - start_pos.y()
            new_width = self.current_ellipse['width'] + int(delta / (5 * self.scale_factor))
            self.current_ellipse['width'] = max(1, min(50, new_width))
            self.drag_start = event.pos()
            self.update_style_editor()
        else:
            # 更新鼠标样式
            cursor = Qt.CursorShape.ArrowCursor
            for ellipse in self.ellipse_marks:
                if self.is_on_ellipse_edge(event.pos(), ellipse):
                    cursor = Qt.CursorShape.SizeHorCursor
                    break
                elif self.is_on_ellipse_border(event.pos(), ellipse):
                    cursor = Qt.CursorShape.SizeVerCursor
                    break
                elif self.is_inside_ellipse(event.pos(), ellipse):
                    cursor = Qt.CursorShape.SizeAllCursor
                    break
            
            # 检查下划线
            for underline in self.underline_marks:
                if self.is_on_underline(event.pos(), underline):
                    cursor = Qt.CursorShape.PointingHandCursor
                    break
                    
            self.setCursor(cursor)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.dragging = False
        self.resizing = False
        self.adjusting_width = False
        self.current_ellipse = None
        self.current_underline = None

    def update_style_editor(self):
        """更新StyleTextEditor中的控制值和标记"""
        if self.style_text_editor and self.current_ellipse:
            # 更新控制面板的值
            self.style_text_editor.position_spin.blockSignals(True)
            self.style_text_editor.size_spin.blockSignals(True)
            self.style_text_editor.width_spin.blockSignals(True)
            
            self.style_text_editor.position_spin.setValue(self.current_ellipse['position'])
            self.style_text_editor.size_spin.setValue(self.current_ellipse['size'])
            self.style_text_editor.width_spin.setValue(self.current_ellipse['width'])
            
            self.style_text_editor.position_spin.blockSignals(False)
            self.style_text_editor.size_spin.blockSignals(False)
            self.style_text_editor.width_spin.blockSignals(False)
            
            # 更新StyleTextEditor中的标记数据
            for (start, end), style in self.style_text_editor.text_marks.items():
                if (start == self.current_ellipse['start'] and 
                    end == self.current_ellipse['end'] and 
                    style['type'] == 'ellipse'):
                    # 更新现有标记的属性
                    style.update({
                        'position': self.current_ellipse['position'],
                        'size': self.current_ellipse['size'],
                        'width': self.current_ellipse['width']
                    })
                    break
            
            # 触发重新生成图片
            self.style_text_editor.style_applied.emit()

    def update_ellipse_marks(self, marks):
        """更新椭圆和下划线标记信息"""
        self.ellipse_marks = []
        self.underline_marks = []
        for (start, end), style in marks.items():
            if style['type'] == 'ellipse':
                self.ellipse_marks.append({
                    'start': start,
                    'end': end,
                    'position': style.get('position', 0),
                    'size': style.get('size', 10),
                    'width': style.get('width', 2),
                    'color': style.get('color', '#000000')
                })
            elif style['type'] == 'underline':
                self.underline_marks.append({
                    'start': start,
                    'end': end,
                    'width': style.get('width', 2),
                    'offset': style.get('offset', 5),
                    'color': style.get('color', '#000000')
                })