import os
import logging
import platform

from PyQt6 import Qsci
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.Qsci import QsciScintilla, QsciAPIs
from PyQt6.QtGui import QColor, QFont, QMouseEvent, QPainter, QPen, QKeyEvent

from CONF.Constant import WORDS
from UTIL.jediLib import JdeiLib
from CONF.LexerMaps import LEXER_MAPS


class SuperQSci(QsciScintilla):
    """
    继承QSciScintilla, 添加IDE功能
    """
    jump_info = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.underlined_word_range = None  # 记录下划线范围
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
        self.setMarginWidth(2, 16)

        # 自动缩进相关设置
        self.setWrapMode(QsciScintilla.WrapMode.WrapWord)
        self.setIndentationGuides(True)
        self.setAutoIndent(True)
        self.setTabWidth(4)
        self.setIndentationsUseTabs(True)

        self.setMargs()

        # 启用代码折叠
        self.setFolding(QsciScintilla.FoldStyle.PlainFoldStyle)

    def setMargs(self):
        # 行号相关设置
        self.setMarginWidth(0, 50)
        self.setMarginsBackgroundColor(QColor("#FFFFFF"))
        self.setMarginsForegroundColor(Qt.GlobalColor.gray)
        self.setFoldMarginColors(QColor("#FFFFFF"), QColor("#FFFFFF"))

    def addUnderlineMark(self, start_pos, end_pos):
        """
        在指定文本范围添加真正的直线下划线（无T型端点）
        """
        if not isinstance(start_pos, int) or not isinstance(end_pos, int):
            raise ValueError("start_pos 和 end_pos 必须是整数")
        if start_pos > end_pos:
            raise ValueError("start_pos 不能大于 end_pos")

        # 先清除旧的下划线
        self.clearUnderlineMarks()

        # 记录新的下划线范围
        self.underlined_word_range = (start_pos, end_pos)

        # 设置下划线样式（INDIC_PLAIN = 0，普通直线）
        self.SendScintilla(QsciScintilla.SCI_INDICSETSTYLE, 2, QsciScintilla.INDIC_PLAIN)
        self.SendScintilla(QsciScintilla.SCI_INDICSETFORE, 2, QColor('#0000FF'))  # 设定为蓝色

        # 关键点：确保指示器正确应用
        self.SendScintilla(QsciScintilla.SCI_SETINDICATORCURRENT, 2)
        self.SendScintilla(QsciScintilla.SCI_INDICATORFILLRANGE, start_pos, end_pos - start_pos)

    def clearUnderlineMarks(self):
        """
        清除当前的下划线标记（优化版）
        """
        if self.underlined_word_range:
            start, end = self.underlined_word_range

            # 仅在存在下划线时执行清除操作
            self.SendScintilla(QsciScintilla.SCI_SETINDICATORCURRENT, 2)
            self.SendScintilla(QsciScintilla.SCI_INDICATORCLEARRANGE, start, end - start)

            # 重置存储的下划线范围
            self.underlined_word_range = None

    def paintEvent(self, event):
        super().paintEvent(event)

        if self.underlined_word_range:
            start_pos, end_pos = self.underlined_word_range

            # 获取起始和结束位置的坐标
            start_x = self.SendScintilla(QsciScintilla.SCI_POINTXFROMPOSITION, 0, start_pos)
            end_x = self.SendScintilla(QsciScintilla.SCI_POINTXFROMPOSITION, 0, end_pos)
            baseline_y = self.SendScintilla(QsciScintilla.SCI_POINTYFROMPOSITION, 0, start_pos) + self.textHeight(0)

            # 手动绘制纯直线下划线
            painter = QPainter(self)
            pen = QPen(QColor('#0000FF'))  # 蓝色
            pen.setWidth(2)  # 线条宽度
            painter.setPen(pen)
            painter.drawLine(start_x, baseline_y, end_x, baseline_y)
            painter.end()

    def positionFromPoint(self, pos):
        pos = self.SendScintilla(QsciScintilla.SCI_POSITIONFROMPOINT, pos.x(), pos.y())
        start = self.SendScintilla(QsciScintilla.SCI_WORDSTARTPOSITION, pos, True)
        end = self.SendScintilla(QsciScintilla.SCI_WORDENDPOSITION, pos, True)
        return start, end

    def mousePressEvent(self, event: QMouseEvent):
        """
        处理鼠标点击事件：
        - 按住 Ctrl + 左键 点击单词：添加蓝色下划线
        - 松开 Ctrl + 左键 再次点击：清除下划线
        """
        if event.button() == Qt.MouseButton.LeftButton:
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                try:
                    pos = event.pos()
                    start, end = self.positionFromPoint(pos)
                    self.addUnderlineMark(start, end)
                    cursor_position = self.getCursorPosition()
                    jedi_lib = JdeiLib(source=self.text(), filename=self.current_file_path)
                    assignment = jedi_lib.getAssignment(line=cursor_position[0] + 1, index=cursor_position[1])
                    references = jedi_lib.getReferences(line=cursor_position[0] + 1, index=cursor_position[1])
                    jump_info = dict(assignment=assignment, references=references)
                    self.jump_info.emit(jump_info)
                except Exception as e:
                    logging.warning(e)
            else:
                # 松开 Ctrl + 左键：清除下划线
                self.clearUnderlineMarks()

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """
        松开鼠标左键时的处理：
        - 松开 Ctrl 后点击左键，清除下划线
        """
        if event.button() == Qt.MouseButton.LeftButton and self.underlined_word_range:
            self.clearUnderlineMarks()

        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        """
        监听键盘事件，自动补全括号和引号
        """
        key = event.key()
        cursor_pos = self.getCursorPosition()

        # 自动补全规则
        pairings = {
            ord('"'): '"',
            ord("'"): "'",
            ord('('): ')',
            ord('['): ']',
            ord('{'): '}',
        }

        if key in pairings:
            self.insert(pairings[key])  # 插入对应的闭合符号
            self.setCursorPosition(cursor_pos[0], cursor_pos[1])  # 让光标回到中间

        super().keyPressEvent(event)

    def loadFile(self, file_path):
        """
        通过文件路径加载文件内容到编辑器
        :param file_path: 要打开的完整文件路径
        """
        print(f'正在加载文件: {file_path}')
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
        self.setMargs()
        self.setAutoCompletionSource(QsciScintilla.AutoCompletionSource.AcsAPIs)
        self.setAutoCompletionThreshold(1)  # 输入1个字符后触发补全
        self.textChanged.connect(self.show_completion)

    def _configureLexer(self, file_path):
        """
        根据文件扩展名配置对应语言的词法分析器，并设置高亮颜色 (PyCharm Light 主题)
        :param file_path: 文件路径，用于判断扩展名
        """
        ext = os.path.splitext(file_path)[1].lower()
        lexer_class = LEXER_MAPS.get(ext, Qsci.QsciLexerPython)

        self.lexer = lexer_class(self)
        self.apis = QsciAPIs(self.lexer)

        # 设置字体，根据操作系统区分
        font_family = 'Monaco' if platform.system() == 'Darwin' else 'Consolas'
        font = QFont(font_family, 11)
        self.lexer.setDefaultFont(font)

        self.lexer.setPaper(QColor('#FFFFFF'))  # 背景色（白色）
        self.lexer.setColor(QColor('#000000'), Qsci.QsciLexerPython.Default)  # 普通文本（黑色）
        self.lexer.setColor(QColor('#0000FF'), Qsci.QsciLexerPython.Keyword)  # 关键字（蓝色）
        self.lexer.setColor(QColor('#808080'), Qsci.QsciLexerPython.Comment)  # 注释（灰色）
        self.lexer.setColor(QColor('#098658'), Qsci.QsciLexerPython.Number)  # 数字（绿色）
        self.lexer.setColor(QColor('#8FBC8F'), Qsci.QsciLexerPython.DoubleQuotedString)  # 双引号字符串（浅绿色）
        self.lexer.setColor(QColor('#8FBC8F'), Qsci.QsciLexerPython.SingleQuotedString)  # 单引号字符串（浅绿色）
        self.lexer.setColor(QColor('#8FBC8F'), Qsci.QsciLexerPython.TripleDoubleQuotedString)  # 三双引号字符串（浅绿色）
        self.lexer.setColor(QColor('#8FBC8F'), Qsci.QsciLexerPython.TripleSingleQuotedString)  # 三双引号字符串（浅绿色）
        self.lexer.setColor(QColor('#000000'), Qsci.QsciLexerPython.Operator)  # 操作符（黑色）
        self.lexer.setColor(QColor('#000000'), Qsci.QsciLexerPython.Identifier)  # 变量名（黑色）
        self.lexer.setColor(QColor('#267f99'), Qsci.QsciLexerPython.ClassName)  # 类名（深蓝色）
        self.lexer.setColor(QColor('#267f99'), Qsci.QsciLexerPython.FunctionMethodName)  # 方法名（深蓝色）
        self.lexer.setColor(QColor('#795E26'), Qsci.QsciLexerPython.Decorator)  # 装饰器（棕色）
        self.lexer.setColor(QColor('#808080'), Qsci.QsciLexerPython.CommentBlock)  # 多行注释（灰色）
        self.lexer.setColor(QColor('#E51400'), Qsci.QsciLexerPython.UnclosedString)  # 未关闭字符串（亮红色）
        self.lexer.setColor(QColor('#267f99'), Qsci.QsciLexerPython.HighlightedIdentifier)  # 高亮变量（深蓝色）

        self.setLexer(self.lexer)
        self.SendScintilla(QsciScintilla.SCI_SETKEYWORDS, 1, WORDS)

    def save_file(self):
        try:
            with open(self.current_file_path, 'w', encoding='utf-8') as file:
                file.write(self.text())
        except Exception as e:
            logging.warning(e)
        finally:
            return

    def show_completion(self):
        self.textChanged.disconnect(self.show_completion)

        cursor_position = self.getCursorPosition()

        # 获取 Jedi 补全建议
        jedi_lib = JdeiLib(source=self.text(), filename=self.current_file_path)
        completions = jedi_lib.getCompletions(line=cursor_position[0] + 1, index=cursor_position[1])

        if completions:  # 确保补全列表有效
            self.apis.clear()  # 清空之前的补全项
            for completion in completions:
                self.apis.add(completion)
            self.apis.prepare()
            self.setAutoCompletionSource(QsciScintilla.AutoCompletionSource.AcsAPIs)
        else:
            print("No completions available.")
        self.textChanged.connect(self.show_completion)

    def move_cursor_visible(self, line, index=0):
        if line:
            self.setCursorPosition(line - 1, index)
            self.ensureLineVisible(line + self.SendScintilla(QsciScintilla.SCI_LINESONSCREEN) // 2)
