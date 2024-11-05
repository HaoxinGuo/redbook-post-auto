import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.styles import FusionStyle

def main():
    app = QApplication(sys.argv)
    
    # 应用 Fusion 风格
    FusionStyle.apply_fusion_style(app)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 