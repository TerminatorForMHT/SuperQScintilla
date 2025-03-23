import logging
import os

from PyQt6 import Qsci
from PyQt6.Qsci import QsciScintilla
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QColor, QFont, QMouseEvent
from PyQt6.QtWidgets import QApplication

from CONF.LexerMaps import LEXER_MAPS


class SuperQSci(QsciScintilla):
    """
    继承QSciScintilla, 添加IDE功能
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.underlined_word_range = None
        self.current_file_path = None
        self._parent = parent
        self.init_ui()

    def init_ui(self):
        # 配置折叠标记样式
        self.markerDefine(QsciScintilla.MarkerSymbol.RightArrow, QsciScintilla.SC_MARKNUM_FOLDEROPEN)
        self.markerDefine(QsciScintilla.MarkerSymbol.RightArrow, QsciScintilla.SC_MARKNUM_FOLDER)
        self.markerDefine(QsciScintilla.MarkerSymbol.Minus, QsciScintilla.SC_MARKNUM_FOLDERSUB)
        self.markerDefine(QsciScintilla.MarkerSymbol.Minus, QsciScintilla.SC_MARKNUM_FOLDERTAIL)
        self.markerDefine(QsciScintilla.MarkerSymbol.Minus, QsciScintilla.SC_MARKNUM_FOLDEREND)
        self.markerDefine(QsciScintilla.MarkerSymbol.Minus, QsciScintilla.SC_MARKNUM_FOLDEROPENMID)

        # 设置折叠边距宽度
        self.setMarginWidth(2, 16)  # 2 表示折叠边距

        # 自动缩进相关设置
        self.setWrapMode(QsciScintilla.WrapMode.WrapWord)  # 使用具体的枚举值
        self.setIndentationGuides(True)
        self.setAutoIndent(True)
        self.setTabWidth(4)
        self.setIndentationsUseTabs(True)  # 使用Tab键进行缩进

        # 行号相关设置
        self.setMarginWidth(0, 50)  # 行号边距宽度
        self.setMarginsBackgroundColor(QColor("#FFFFFF"))  # 设置行号边距背景色为白色
        self.setMarginsForegroundColor(Qt.GlobalColor.gray)
        self.setFoldMarginColors(QColor("#FFFFFF"), QColor("#FFFFFF"))

        # 启用代码折叠
        self.setIndentationGuides(True)
        self.setFolding(QsciScintilla.FoldStyle.PlainFoldStyle)  # 代码块折叠相关设置
        self.markerDefine(QsciScintilla.MarkerSymbol.Minus, QsciScintilla.SC_MARKNUM_FOLDEROPEN)
        self.markerDefine(QsciScintilla.MarkerSymbol.Plus, QsciScintilla.SC_MARKNUM_FOLDER)

        self.setMarkerBackgroundColor(QColor("#0078D7"), QsciScintilla.SC_MARKNUM_FOLDER)
        self.setMarkerForegroundColor(QColor("#FFFFFF"), QsciScintilla.SC_MARKNUM_FOLDER)
        self.setMarkerBackgroundColor(QColor("#0078D7"), QsciScintilla.SC_MARKNUM_FOLDEROPEN)
        self.setMarkerForegroundColor(QColor("#FFFFFF"), QsciScintilla.SC_MARKNUM_FOLDEROPEN)

    def addUnderlineMark(self, start_pos, end_pos, line_type=2):
        """
        在指定文本范围添加下划线标记
        :param start_pos: 起始字符位置
        :param end_pos: 结束字符位置
        :param line_type: 下划线类型 (0: 代表错误的红色波浪线, 1: 代表警告的黄色波浪线,2: 代表点击选中的蓝色直线框)
        """
        # 参数校验
        if not isinstance(start_pos, int) or not isinstance(end_pos, int):
            raise ValueError("start_pos 和 end_pos 必须是整数")
        if start_pos > end_pos:
            raise ValueError("start_pos 不能大于 end_pos")

        if line_type == 0:
            color = QColor('#FF0000')
            style = QsciScintilla.INDIC_SQUIGGLE  # 波浪线
        elif line_type == 1:
            color = QColor('#FFFF00')
            style = QsciScintilla.INDIC_SQUIGGLE  # 波浪线
        elif line_type == 2:
            color = QColor('#0000FF')
            style = QsciScintilla.INDIC_STRAIGHTBOX  # 直线
        else:
            raise ValueError("不支持的标记类型！")

        self.SendScintilla(QsciScintilla.SCI_INDICSETSTYLE, 2, style)  # 设置指示器样式
        self.SendScintilla(QsciScintilla.SCI_INDICSETFORE, style, color)
        self.SendScintilla(QsciScintilla.SCI_INDICATORFILLRANGE, start_pos, end_pos - start_pos)

    def clearUnderlineMarks(self):
        """
        清除指定范围内的下划线标记
        :param start_pos: 起始字符位置（None表示文档开头）
        :param end_pos: 结束字符位置（None表示文档末尾）
        """
        if self.underlined_word_range:
            start, end = self.underlined_word_range
            self.SendScintilla(QsciScintilla.SCI_INDICATORCLEARRANGE, start, end - start)
            self.underlined_word_range = None

    def loadFile(self, file_path):
        """
        通过文件路径加载文件内容到编辑器
        :param file_path: 要打开的完整文件路径
        """
        self.current_file_path = file_path
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.setText(content)
        except Exception as e:
            print(f"未知错误: {e}")

        self._configureLexer(file_path)

    def _configureLexer(self, file_path):
        """
        根据文件扩展名配置对应语言的词法分析器
        :param file_path: 文件路径，用于判断扩展名
        """

        ext = os.path.splitext(file_path)[1].lower()
        lexer_class = LEXER_MAPS.get(ext, Qsci.QsciLexerPython)

        self.lexer = lexer_class(self)
        self.lexer.setDefaultFont(QFont('Consolas', 10))
        self.lexer.setPaper(QColor('#FFFFFF'))
        self.setLexer(self.lexer)

    def positionFromPoint(self, pos):
        # 将像素位置转换为文本位置
        pos = self.SendScintilla(QsciScintilla.SCI_POSITIONFROMPOINT, pos.x(), pos.y())
        start = self.SendScintilla(QsciScintilla.SCI_WORDSTARTPOSITION, pos, True)
        end = self.SendScintilla(QsciScintilla.SCI_WORDENDPOSITION, pos, True)
        return start, end

    def mousePressEvent(self, event: QMouseEvent):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.button() == Qt.MouseButton.LeftButton:
            self.clearUnderlineMarks()
            try:
                pos = event.pos()
                start, end = self.positionFromPoint(pos)  # 获取文本位置
                self.underlined_word_range = (start, end)
                self.addUnderlineMark(start, end, line_type=2)
            except Exception as e:
                logging.warning(e)
        else:
            super().mousePressEvent(event)

    def save_file(self):
        try:
            with open(self.current_file_path, 'w', encoding='utf-8') as file:
                file.write(self.text())
        except Exception as e:
            logging.warning(e)
        finally:
            return
