import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from ui.main_window import MainWindow
from ui.styles import FusionStyle
import os

def resource_path(relative_path):
    """获取资源文件的绝对路径"""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def main():
    app = QApplication(sys.argv)
    
    # 设置应用程序图标
    icon_path = resource_path(os.path.join('resources', 'icon.png'))
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # 应用样式
    
    FusionStyle.apply_fusion_style(app)
    # 如果有 QSS 文件
    style_path = resource_path('resources/styles.qss')
    if os.path.exists(style_path):
        with open(style_path, 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 