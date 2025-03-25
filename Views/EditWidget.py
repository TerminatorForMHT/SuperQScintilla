import os
from pathlib import PurePath

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QIcon, QCursor
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QStackedWidget
from qfluentwidgets import TabBar, RoundMenu, Action

from CONF.Constant import IMG_PATH
from Views.SuperQSci import SuperQSci


class EditWidget(QFrame):
    """
    多Tab多开编辑框组件
    """
    file_save = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.tab_texts = list()
        self.load_file_dict = dict()

        self.initUi()

    def initUi(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

        self.tab_bar = TabBar()
        self.tab_bar.setAddButtonVisible(False)
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet('margin: 2px;')

        self.main_layout.addWidget(self.tab_bar)
        self.main_layout.addWidget(self.stacked_widget)

        self.tab_bar.tabCloseRequested.connect(self.closeTab)
        self.tab_bar.tabBarClicked.connect(self.switchTab)
        # 调整 TabBar 和 Editor 的间距
        self.stacked_widget.setStyleSheet('QStackedWidget { margin-top: -3px; }')

        # 设置背景色为白色
        self.setStyleSheet('background-color: white;')

    def loadFile(self, file_path):
        if file_path not in self.load_file_dict.keys():
            editor = SuperQSci(self)
            editor.loadFile(file_path)
            editor.jump_info.connect(self.handleCtrlLeftClick)
            editor.file_save.connect(self.saveFile)
            self.stacked_widget.addWidget(editor)
            index = self.stacked_widget.count() - 1
            tab_text = file_path.split(os.sep)[-1]
            if tab_text in self.tab_texts:
                self.tab_texts.append(tab_text)
                tab_text = f'{file_path.split(os.sep)[-2]}{os.sep}{tab_text}'
                self.tab_bar.addTab(file_path, tab_text)
            else:
                self.tab_texts.append(tab_text)
                self.tab_bar.addTab(file_path, tab_text)
            self.tab_bar.setCurrentTab(file_path)
            self.stacked_widget.setCurrentWidget(editor)
            self.load_file_dict[file_path] = index
            return editor
        else:
            index = self.load_file_dict.get(file_path)
            self.tab_bar.setCurrentTab(file_path)
            self.stacked_widget.setCurrentIndex(index)
            editor = self.stacked_widget.currentWidget()
            return editor

    def closeTab(self, index):
        if self.stacked_widget.count() > 0:
            widget = self.stacked_widget.widget(index)
            file_path = widget.current_file_path
            self.tab_texts.remove(file_path.split(os.sep)[-1])
            del self.load_file_dict[file_path]
            self.stacked_widget.removeWidget(widget)
            self.tab_bar.removeTab(index)

    def switchTab(self, index):
        self.stacked_widget.setCurrentIndex(index)

    def jumpToAssignTab(self, file_path, line, index):
        editor = self.loadFile(file_path)
        editor.moveCursorVisible(line, index)

    def jumpToAssignLine(self, line, index):
        widget = self.stacked_widget.currentWidget()
        if isinstance(widget, SuperQSci):
            widget.moveCursorVisible(line, index)

    def referenceJump(self, jump_info: dict):
        path, line, column = jump_info['ModulePath'], jump_info['Line'], jump_info['Column']
        self.jumpToAssignTab(path, line, column)

    def showReferenceMenu(self, reference_addr):
        menu = RoundMenu()
        icon = str(IMG_PATH.joinpath(PurePath('python.png')))
        for item in reference_addr:
            file = item['ModulePath'].split(os.sep)[-1]
            line, code = item.get('Line'), item.get('Code')
            item_info = f'{file}    {line}   {code}'
            menu.addAction(Action(QIcon(icon), item_info, triggered=lambda: self.referenceJump(item)))
        menu.exec(QCursor.pos())

    def handleCtrlLeftClick(self, info: dict):
        assign_addr = info.get("assignment")
        reference_addr = info.get("references")
        if assign_addr:
            path, line, index = assign_addr.get('ModulePath'), assign_addr.get('Line'), assign_addr.get('Column')
            current_tab = self.stacked_widget.currentWidget()
            if path != current_tab.current_file_path:
                self.jumpToAssignTab(path, line, index)
            else:
                self.jumpToAssignLine(line, index)
        elif reference_addr:
            if len(reference_addr) == 1:
                self.referenceJump(reference_addr[0])
            elif len(reference_addr) > 1:
                self.showReferenceMenu(reference_addr)

    def saveFile(self, file_path: str):
        self.file_save.emit(file_path)
