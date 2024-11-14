try:
    # 首先尝试相对导入（当作为包的一部分导入时）
    from .text_editor import TextEditor
    from .style_panel import StylePanel
    from .styles import FusionStyle
    from .style_text_editor import StyleTextEditor
except ImportError:
    # 如果相对导入失败，使用绝对导入（当直接运行文件时）
    from ui.text_editor import TextEditor
    from ui.style_panel import StylePanel
    from ui.styles import FusionStyle
    from ui.style_text_editor import StyleTextEditor

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QTabWidget, QTextEdit, QPushButton, QComboBox, 
                           QRadioButton, QLabel, QScrollArea, QFileDialog, 
                           QSizePolicy, QFrame, QMessageBox)
from PyQt6.QtCore import Qt, QSize, QPoint
from PyQt6.QtGui import QPixmap, QResizeEvent, QIcon, QPainter, QPen, QColor
from core.image_generator import ImageGenerator
from core.ai_helper import AIHelper
import asyncio
import os
import json
from datetime import datetime
from PIL import Image
from PyQt6.QtCore import QTimer
from PIL import ImageDraw
from PIL import ImageFont
import sys
import tempfile
import time

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
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)  # 设置按钮之间的间距
        
        # 生成按钮
        self.generate_button = QPushButton("生成图片")
        self.generate_button.setObjectName("primaryButton")
        self.generate_button.setMinimumHeight(40)
        self.generate_button.clicked.connect(self.generate_image)
        
        # 下载按钮
        self.download_button = QPushButton("下载所有图片")
        self.download_button.setEnabled(False)
        self.download_button.setObjectName("primaryButton")
        self.download_button.setMinimumHeight(40)
        self.download_button.clicked.connect(self.download_images)
        
        # 下载文档按钮
        self.download_text_button = QPushButton("下载文档")
        self.download_text_button.setEnabled(False)  # 初始状态禁用
        self.download_text_button.setObjectName("primaryButton")
        self.download_text_button.setMinimumHeight(40)
        self.download_text_button.clicked.connect(self.download_text_document)
        
        # 添加按钮到布局
        button_layout.addWidget(self.generate_button)
        button_layout.addWidget(self.download_button)
        button_layout.addWidget(self.download_text_button)
        
        # 设置按钮容器的大小策略
        button_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
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
        
        # 建预览内容容器
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
        
        # 将预览标和按钮添加到预览内容布局
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
            print("\n=== 开始生成图片 ===")
            style = self.style_panel.get_current_style()
            bg_value = style['background']
            bg_config = next((bg for bg in self.style_panel.config['backgrounds'] 
                            if bg['value'] == bg_value), None)
            bg_path = bg_config['url'] if bg_config else None
            
            print(f"背景路径: {bg_path}")
            
            # 获取当前激活的标签页
            current_tab = self.tabs.currentWidget()
            print(f"当前标签页类型: {type(current_tab)}")
            
            if current_tab == self.style_text_tab:
                print("处理封面编辑内容")
                content = self.style_text_editor.get_content()
                print(f"封面编辑内容: {content}")
                
                # 创建单页图片
                image = Image.new('RGB', (self.image_generator.width, self.image_generator.height), 'white')
                print("创建新图片")
                
                # 加载背景
                if bg_path:
                    try:
                        bg = Image.open(bg_path)
                        bg = bg.resize((self.image_generator.width, self.image_generator.height))
                        image.paste(bg, (0, 0))
                        print("背景加载成功")
                    except Exception as e:
                        print(f"加载背景图片失败: {str(e)}")
                
                # 创建绘图对象
                draw = ImageDraw.Draw(image)
                print("创建绘图对象")
                
                # 获取字体大小和加粗状态
                font_size = content.get('font_size', 48)
                is_bold = content.get('font_bold', False)
                print(f"字体大小: {font_size}, 是否加粗: {is_bold}")
                
                # 创建字体对象，传入加粗参数
                font = self.image_generator.create_font(font_size, is_bold)
                print(f"字体对象创建完成: {font}")
                
                # 绘制文字
                self.image_generator.draw_styled_text(
                    draw,
                    content['text'],
                    content['marks'],
                    0,
                    0,
                    font,
                    char_spacing=content.get('char_spacing', 0),
                    line_spacing=content.get('line_spacing', 20)
                )
                print("文本绘制完成")
                
                # 添加 logo
                try:
                    # 获取 logo 路径
                    if hasattr(sys, '_MEIPASS'):
                        logo_path = os.path.join(sys._MEIPASS, 'resources/icons', 'logo.png')
                    else:
                        logo_path = os.path.join('resources/icons', 'logo.png')
                    
                    print(f"\n=== 添加 Logo ===")
                    print(f"Logo 路径: {logo_path}")
                    print(f"Logo 文件是否存在: {os.path.exists(logo_path)}")
                    print(f"当前工作目录: {os.getcwd()}")
                    print(f"resources 目录内容:")
                    try:
                        for item in os.listdir('resources'):
                            print(f"  - {item}")
                    except Exception as e:
                        print(f"无法列出 resources 目录内容: {str(e)}")
                    
                    if os.path.exists(logo_path):
                        # 加载 logo
                        logo = Image.open(logo_path)
                        print(f"Logo 模式: {logo.mode}")
                        print(f"Logo 尺寸: {logo.size}")
                        
                        # 设置 logo 大小
                        logo_height = 60  # logo 的目标高度
                        aspect_ratio = logo.width / logo.height
                        logo_width = int(logo_height * aspect_ratio)
                        
                        # 调整 logo 大小
                        logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
                        print(f"调整后的 Logo 尺寸: {logo.size}")
                        
                        # 计算 logo 位置（左下角，留出边距）
                        margin = 20  # 边距
                        x = margin
                        y = self.image_generator.height - logo_height - margin
                        print(f"Logo 位置: ({x}, {y})")
                        
                        # 如果 logo 有透明通道，需要特殊处理
                        if logo.mode == 'RGBA':
                            print("处理带透明通道的 Logo")
                            # 将原图转换为 RGBA 模式
                            image = image.convert('RGBA')
                            # 创建一个与原图大小相同的透明图层
                            overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
                            # 将 logo 粘贴到透明图层上
                            overlay.paste(logo, (x, y))
                            # 将透明图层与原图合并
                            image = Image.alpha_composite(image, overlay)
                            # 转换回 RGB 模式
                            image = image.convert('RGB')
                        else:
                            print("处理不带透明通道的 Logo")
                            # 如果 logo 没有透明通道，直接粘贴
                            image.paste(logo, (x, y))
                            
                        print("Logo 添加成功")
                    else:
                        print(f"Logo 文件不存在: {logo_path}")
                        
                except Exception as e:
                    print(f"添加 Logo 失败: {str(e)}")
                    import traceback
                    traceback.print_exc()
                
                self.current_images = [image]
                print("图片生成完成")
                
            else:
                print("处理普通文本编辑内容")
                content = self.text_editor.get_all_content()
                self.current_images = self.image_generator.create_images(
                    content,
                    bg_path,
                    style['font_style']
                )
            
            # 更新预览
            self.current_image_index = 0
            print("开始更新预览")
            self.update_preview()
            print("预览更新完成")
            
            # 更新按钮状态
            self.update_navigation_buttons()
            self.download_button.setEnabled(True)
            self.download_text_button.setEnabled(True)
            
            print(f"生成了 {len(self.current_images)} 张图片")
            print("=== 图片生成完成 ===\n")
            
        except Exception as e:
            print(f"生成图片错误: {str(e)}")
            import traceback
            traceback.print_exc()
            self.preview_label.setText("生成图片失败")
            self.download_button.setEnabled(False)
            self.download_text_button.setEnabled(False)
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
    
    def update_preview(self):
        """更新预览图片"""
        if not self.current_images or self.current_image_index >= len(self.current_images):
            print("没有可预览的图片")
            return
            
        try:
            # 在系统临时目录创建临时文件
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_path = temp_file.name
                
            print(f"使用临时文件路径: {temp_path}")
            
            # 保存图片到临时文件
            self.current_images[self.current_image_index].save(temp_path, 'PNG')
            print(f"图片已保存到临时文件")
            
            # 强制刷新文件到磁盘
            import time
            time.sleep(0.1)  # 给文件系统一点时间
            
            # 加载图片
            pixmap = QPixmap(temp_path)
            if pixmap.isNull():
                print("预览图片加载失败")
                print(f"检查临时文件是否存在: {os.path.exists(temp_path)}")
                print(f"临时文件大小: {os.path.getsize(temp_path) if os.path.exists(temp_path) else 'file not found'}")
                return
                
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
            print("预览图片更新成功")
            
            # 清理临时文件
            try:
                os.remove(temp_path)
                print("临时预览文件已清理")
            except Exception as e:
                print(f"清理临时文件败: {str(e)}")
                
        except Exception as e:
            print(f"更新预览失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
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
            QMessageBox.warning(self, "导出失败", "没有可下载的图片")
            return
            
        try:
            # 获取当前标签页
            current_tab = self.tabs.currentWidget()
            
            # 选保存目录
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
                    
                    # 显示成功消息
                    QMessageBox.information(
                        self,
                        "导出成功",
                        f"成功导出 1 张封面图片\n保存路径：{filepath}"
                    )
                    
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
                    saved_count = 0
                    for i, image in enumerate(self.current_images):
                        try:
                            filename = f"{safe_title}_{i + 1}.png"
                            filepath = os.path.join(folder_path, filename)
                            image.save(filepath, 'PNG')
                            saved_count += 1
                        except Exception as e:
                            print(f"保存图片 {i + 1} 失败: {str(e)}")
                    
                    # 显示成功消息
                    if saved_count == len(self.current_images):
                        QMessageBox.information(
                            self,
                            "导出成功",
                            f"成功导出 {saved_count} 张图片\n保存路径：{folder_path}"
                        )
                    else:
                        QMessageBox.warning(
                            self,
                            "部分导出成功",
                            f"成功导出 {saved_count}/{len(self.current_images)} 张图片\n保存路径：{folder_path}"
                        )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "导出失败",
                f"保存图片时发生错误：\n{str(e)}"
            )
    
    def preview_style_change(self, style):
        """当样式改变时更新预览"""
        if self.current_images:
            # 如果已经生成了图片，则新生成
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
        # 使用 iPhone 15 Pro 的显示比例
        preview_width = int(1080 * self.preview_label.default_zoom)
        preview_height = int(1440 * self.preview_label.default_zoom)
        
        # 更新预览标签的固定大小
        self.preview_label.setFixedSize(QSize(preview_width, preview_height))
    
    def update_preview_size(self):
        """更新预览图片大小"""
        # 让 PreviewLabel 自己处理缩放
        self.preview_label.update_preview_size()
        
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
                # bg_config['url'] 现在应该已经是完整路径
                bg_path = bg_config['url']
                print(f"加载背景图片: {bg_path}")
                    
                if not os.path.exists(bg_path):
                    print(f"背景图片不存在: {bg_path}")
                    self.preview_label.clear()
                    return
                    
                # 加载背景图片
                pixmap = QPixmap(bg_path)
                if pixmap.isNull():
                    print("背景图片加载失败")
                    self.preview_label.clear()
                    return
                    
                # 获取预览标签的大小
                label_size = self.preview_label.size()
                
                # 缩放图片以填充预览标签，保持宽高比
                scaled_pixmap = pixmap.scaled(
                    label_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                # 显示预��
                self.preview_label.setPixmap(scaled_pixmap)
                print("背景图片加载成功")
            else:
                # 如果没有背景配置，显示空白
                self.preview_label.clear()
                
        except Exception as e:
            print(f"背景预览错误: {str(e)}")
            import traceback
            traceback.print_exc()
            self.preview_label.clear()
    
    def on_style_text_changed(self):
        """当样式文本编辑器的内容改变时"""
        # 移除自动生成图片的逻辑，只在点击生成按钮时生成
        pass

    def download_text_document(self):
        """下载文本内容到txt文件"""
        try:
            # 获取所有内容
            content = self.text_editor.get_all_content()
            
            # 获取标题
            title = "未命名"
            for item in content:
                if item['type'] == 'title' and item.get('text', '').strip():
                    title = item['text'].strip()
                    break
            
            # 去除可能存在的非法文件名字符
            safe_title = "".join(c for c in title if c not in r'\/:*?"<>|')
            
            # 选择保存目录
            directory = QFileDialog.getExistingDirectory(
                self,
                "选择保存目录",
                "",
                QFileDialog.Option.ShowDirsOnly
            )
            
            if directory:
                # 创建文件名
                filename = f"{safe_title}.txt"
                filepath = os.path.join(directory, filename)
                
                # 准备文本内容
                text_content = []
                for item in content:
                    if item.get('text', '').strip():
                        # 根据类型加不同的格式
                        if item['type'] == 'title':
                            text_content.append(f"{item['text']}\n")
                        else:
                            text_content.append(f"{item['text']}\n")
                        text_content.append("\n")  # 添加空行分隔
                
                # 写入文件
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.writelines(text_content)
                
                # 显示成功消息
                QMessageBox.information(
                    self,
                    "导出成功",
                    f"文档已保存到：\n{filepath}"
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "导出失败",
                f"保存文档时发生错误：\n{str(e)}"
            )

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
        
        self._original_pixmap = None  # 添加这行来存储原始图片
        self.zoom_factor = 1.0
        self.iphone_width = 1179
        self.iphone_height = 2556
        self.min_zoom = 0.2
        self.max_zoom = 2.0
        
        # 设置默认缩放以适应 iPhone 显示效果
        self.default_zoom = min(
            self.iphone_width / 1080,
            self.iphone_height / 1440
        ) * 0.4
        self.zoom_factor = self.default_zoom
        
        self.setFocusPolicy(Qt.FocusPolicy.WheelFocus)

    def setPixmap(self, pixmap):
        """重写setPixmap方法以应用缩放"""
        if pixmap:
            self._original_pixmap = pixmap
            self.update_preview_size()
        else:
            self._original_pixmap = None
            super().setPixmap(None)

    def update_preview_size(self):
        """更新预览图片大小"""
        if not self._original_pixmap:
                    return

        # 计算缩放后的尺寸
        scaled_width = int(1080 * self.zoom_factor)
        scaled_height = int(1440 * self.zoom_factor)
        
        # 设置固定大小
        self.setFixedSize(scaled_width, scaled_height)
        
        # 缩放图片
        scaled_pixmap = self._original_pixmap.scaled(
            scaled_width,
            scaled_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # 使用父类的setPixmap方法来避免递归
        super().setPixmap(scaled_pixmap)
        
        # 更新缩放因子
        self.scale_factor = scaled_width / 1080

    def wheelEvent(self, event):
        """处理鼠标滚轮事件实现缩放"""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            zoom_delta = 1.1 if delta > 0 else 0.9
            
            # 计算新的缩放比例
            new_zoom = self.zoom_factor * zoom_delta
            
            # 限制缩放范围
            if self.min_zoom <= new_zoom <= self.max_zoom:
                self.zoom_factor = new_zoom
                self.update_preview_size()
                event.accept()
                return
                
        super().wheelEvent(event)