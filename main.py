import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog

from Views.EditWidget import EditWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('SuperQScintilla 编辑器')
        self.setGeometry(100, 100, 800, 600)
        
        # 创建编辑器实例
        self.editor = EditWidget(self)
        self.setCentralWidget(self.editor)
        
        # 创建菜单栏
        menubar = self.menuBar()
        file_menu = menubar.addMenu('文件(&F)')
        
        # 添加打开文件动作
        open_action = file_menu.addAction('打开(&O)')
        open_action.triggered.connect(self.open_file)
        
        # 添加退出动作
        exit_action = file_menu.addAction('退出(&X)')
        exit_action.triggered.connect(self.close)
        
        # 状态栏
        self.statusBar().showMessage('就绪')

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, '打开文件', '', 'All Files (*)')
        if file_path:
            try:
                self.editor.loadFile(file_path)
                self.statusBar().showMessage(f'已加载: {file_path}', 5000)
            except Exception as e:
                self.statusBar().showMessage(f'加载失败: {str(e)}', 5000)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())