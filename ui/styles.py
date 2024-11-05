from PyQt6.QtWidgets import QStyleFactory
from PyQt6.QtGui import QPalette, QColor, QFont
from PyQt6.QtCore import Qt

class FusionStyle:
    # Alibaba Fusion 配色方案
    PRIMARY_COLOR = "#1677FF"  # 主色
    PRIMARY_HOVER = "#4096FF"  # 主色悬停
    PRIMARY_ACTIVE = "#0958D9"  # 主色激活
    SECONDARY_COLOR = "#F5F5F5"  # 次要按钮背景色
    BORDER_COLOR = "#D9D9D9"  # 边框颜色
    TEXT_COLOR = "#2A2A2A"  # 主文本色
    BACKGROUND_COLOR = "#FFFFFF"  # 背景色
    
    @staticmethod
    def apply_fusion_style(app):
        """应用 Fusion 风格到整个应用"""
        app.setStyle(QStyleFactory.create("Fusion"))
        
        # 设置应用字体
        font = QFont("Microsoft YaHei UI", 9)
        app.setFont(font)
        
        # 创建调色板
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(FusionStyle.BACKGROUND_COLOR))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(FusionStyle.TEXT_COLOR))
        palette.setColor(QPalette.ColorRole.Base, QColor(FusionStyle.BACKGROUND_COLOR))
        palette.setColor(QPalette.ColorRole.Text, QColor(FusionStyle.TEXT_COLOR))
        palette.setColor(QPalette.ColorRole.Button, QColor(FusionStyle.SECONDARY_COLOR))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(FusionStyle.TEXT_COLOR))
        app.setPalette(palette)
        
        # 设置样式表
        app.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #D9D9D9;
                border-radius: 4px;
                background-color: #FFFFFF;
                color: #2A2A2A;
                min-height: 20px;
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
                color: #00000040;
                border-color: #D9D9D9;
            }
            
            QPushButton#primaryButton {
                background-color: #1677FF;
                color: white;
                border: none;
            }
            
            QPushButton#primaryButton:hover {
                background-color: #4096FF;
            }
            
            QPushButton#primaryButton:pressed {
                background-color: #0958D9;
            }
            
            QTextEdit {
                border: 1px solid #D9D9D9;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
            }
            
            QComboBox {
                border: 1px solid #D9D9D9;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
                color: #2A2A2A;
                selection-background-color: transparent;
            }
            
            QComboBox:hover {
                border-color: #4096FF;
            }
            
            QComboBox:focus {
                border-color: #4096FF;
                outline: none;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                image: url(resources/icons/down-arrow.png);
                width: 12px;
                height: 12px;
            }
            
            QComboBox QAbstractItemView {
                border: 1px solid #D9D9D9;
                border-radius: 4px;
                background-color: white;
                selection-background-color: #F5F5F5;
                selection-color: #2A2A2A;
                outline: none;
            }
            
            QComboBox QAbstractItemView::item {
                height: 30px;
                padding: 4px 8px;
                color: #2A2A2A;
            }
            
            QComboBox QAbstractItemView::item:hover {
                background-color: #E6F4FF;
                color: #2A2A2A;
            }
            
            QComboBox QAbstractItemView::item:selected {
                background-color: #F0F5FF;
                color: #1677FF;
            }
            
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            
            QLabel {
                color: #2A2A2A;
            }
            
            QTabWidget::pane {
                border: 1px solid #D9D9D9;
                border-radius: 4px;
            }
            
            QTabBar::tab {
                padding: 8px 16px;
                margin-right: 4px;
                background-color: #F5F5F5;
                border: 1px solid #D9D9D9;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #1677FF;
            }
            
            QTabBar::tab:hover {
                background-color: #E6E6E6;
            }
            
            /* 滚动条样式 */
            QScrollBar:vertical {
                border: none;
                background: #F5F5F5;
                width: 8px;
                border-radius: 4px;
            }

            QScrollBar::handle:vertical {
                background: #D9D9D9;
                border-radius: 4px;
                min-height: 20px;
            }

            QScrollBar::handle:vertical:hover {
                background: #BFBFBF;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
            }
        """)