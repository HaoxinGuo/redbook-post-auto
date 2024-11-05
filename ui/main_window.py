from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QTabWidget, QTextEdit, QPushButton, QComboBox, 
                           QRadioButton, QLabel, QScrollArea, QFileDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from .text_editor import TextEditor
from .style_panel import StylePanel
from core.image_generator import ImageGenerator
from core.ai_helper import AIHelper
import asyncio
import os
import json
from datetime import datetime

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("小红书文字转图片 AI 工具")
        self.setMinimumSize(1200, 800)
        self.image_generator = ImageGenerator()
        self.ai_helper = AIHelper()
        self.current_images = []  # 改为列表存储多个图片
        self.current_image_index = 0  # 当前显示的图片索引
        self.init_ui()
        
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
        
        # AI助写标签页
        ai_tab = QWidget()
        ai_layout = QVBoxLayout(ai_tab)
        self.ai_input = QTextEdit()
        self.ai_polish_button = QPushButton("AI 分段润色")
        ai_layout.addWidget(self.ai_input)
        ai_layout.addWidget(self.ai_polish_button)
        ai_tab.setLayout(ai_layout)
        
        # 手动录入标签页
        manual_tab = QWidget()
        manual_layout = QVBoxLayout(manual_tab)
        self.text_editor = TextEditor()
        manual_layout.addWidget(self.text_editor)
        manual_tab.setLayout(manual_layout)
        
        # 添加标签页
        tabs.addTab(ai_tab, "AI 助写")
        tabs.addTab(manual_tab, "手动录入")
        
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
        main_layout.addWidget(left_panel, 40)
        main_layout.addWidget(right_scroll, 60)
        
        # 连接信号
        self.generate_button.clicked.connect(self.generate_image)
        self.ai_polish_button.clicked.connect(self.polish_text)
        self.style_panel.style_changed.connect(self.preview_style_change)
        
    def generate_image(self):
        try:
            style = self.style_panel.get_current_style()
            current_tab = self.findChild(QTabWidget).currentWidget()
            
            if isinstance(current_tab.layout().itemAt(0).widget(), QTextEdit):
                text = self.ai_input.toPlainText()
                content = [{'type': 'content', 'text': text}]
            else:
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
        scaled_pixmap = pixmap.scaled(self.preview_label.size(), 
                                    Qt.AspectRatioMode.KeepAspectRatio,
                                    Qt.TransformationMode.SmoothTransformation)
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
    
    async def polish_text(self):
        try:
            self.ai_polish_button.setEnabled(False)
            self.ai_polish_button.setText("处理中...")
            
            text = self.ai_input.toPlainText()
            if not text.strip():
                return
                
            polished_text = await self.ai_helper.polish_text(text)
            
            # 切换到手动录入标签页
            tab_widget = self.findChild(QTabWidget)
            tab_widget.setCurrentIndex(1)
            
            # 更新文本编辑器内容
            try:
                content = json.loads(polished_text)
                self.text_editor.set_all_content(content)
            except:
                # 如果解析失败，作为普通文本处理
                self.text_editor.set_all_content([{
                    'type': 'content',
                    'text': polished_text
                }])
                
        except Exception as e:
            print(f"AI处理错误: {str(e)}")
        finally:
            self.ai_polish_button.setEnabled(True)
            self.ai_polish_button.setText("AI 分段润色")
    
    def preview_style_change(self, style):
        """当样式改变时更新预览"""
        self.generate_image()