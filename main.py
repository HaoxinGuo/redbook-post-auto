import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from ui.main_window import MainWindow
import os

def main():
    app = QApplication(sys.argv)
    
    # 设置应用程序图标
    icon_path = os.path.join('resources', 'icon.png')  # 确保这个路径存在
    app.setWindowIcon(QIcon(icon_path))
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 