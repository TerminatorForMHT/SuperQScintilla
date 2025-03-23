from PyQt6 import Qsci

LEXER_MAPS = {
    '.py': Qsci.QsciLexerPython,
    '.js': Qsci.QsciLexerJavaScript,
    '.cpp': Qsci.QsciLexerCPP,
    '.html': Qsci.QsciLexerHTML,
    '.java': Qsci.QsciLexerJava,
    '.cs': Qsci.QsciLexerCSharp,
    '.css': Qsci.QsciLexerCSS,
    '.xml': Qsci.QsciLexerXML,
    '.yaml': Qsci.QsciLexerYAML,
    '.md': Qsci.QsciLexerMarkdown,
    '.sql': Qsci.QsciLexerSQL,
    '.sh': Qsci.QsciLexerBash,
    '.json': Qsci.QsciLexerJSON,
    '.rb': Qsci.QsciLexerRuby,
}
