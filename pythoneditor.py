# -------------------------------------------------------------------------
# pythoneditor.py
#
# QScintilla  with PyQt
#
# Eli Bendersky (eliben@gmail.com)
# This code is in the public domain
# -------------------------------------------------------------------------
import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import QFont, QFontMetrics, QColor
from PyQt5.QtWidgets import QApplication
from PyQt5.Qsci import QsciScintilla, QsciLexerPython

FONT_NAME_b = b'Source Code Pro'
FONT_NAME = 'Source Code Pro'
FONT_SIZE = 10  # pt

class PythonEditor(QsciScintilla):
    ARROW_MARKER_NUM = 8

    def __init__(self, parent=None):
        super(PythonEditor, self).__init__(parent)

        self.filename = 'untitled.py'

        # Set the default font
        font = QFont()
        font.setFamily(FONT_NAME)
        font.setFixedPitch(True)
        font.setPointSize(FONT_SIZE)
        self.setFont(font)
        self.setMarginsFont(font)

        # Margin 0 is used for line numbers
        fontmetrics = QFontMetrics(font)
        self.setMarginsFont(font)
        self.setMarginWidth(0, fontmetrics.width("00000") + 6)
        self.setMarginLineNumbers(0, True)
        self.setMarginsBackgroundColor(QColor("#cccccc"))

        # Clickable margin 1 for showing markers
        self.setMarginSensitivity(1, True)
        self.marginClicked.connect(self.on_margin_clicked)
        self.markerDefine(QsciScintilla.RightArrow,
                          self.ARROW_MARKER_NUM)
        self.setMarkerBackgroundColor(QColor("#ee1111"),
                                      self.ARROW_MARKER_NUM)

        # Brace matching: enable for a brace immediately before or after
        # the current position
        #
        self.setBraceMatching(QsciScintilla.SloppyBraceMatch)

        # Current line visible with special background color
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QColor("#ffe4e4"))

        # Set Python lexer
        lexer = QsciLexerPython()
        lexer.setDefaultFont(font)
        self.setLexer(lexer)

        # Set style for Python comments (style number 1) to a fixed-width font.
        self.SendScintilla(QsciScintilla.SCI_STYLESETFONT, 1, FONT_NAME_b)
        self.SendScintilla(QsciScintilla.SCI_STYLESETSIZE, 1, FONT_SIZE)

        # Don't want to see the horizontal scrollbar at all
        # Use raw message to Scintilla here (all messages are documented
        # here: http://www.scintilla.org/ScintillaDoc.html)
        self.SendScintilla(QsciScintilla.SCI_SETHSCROLLBAR, 1)

        # not too small
        self.setMinimumSize(600, 450)

    @pyqtSlot(int, int, Qt.KeyboardModifiers)
    def on_margin_clicked(self, nmargin, nline, modifiers):

        # Toggle marker for the line the margin was clicked on
        # if self.markersAtLine(nline) != 0:
        #     self.markerDelete(nline, self.ARROW_MARKER_NUM)
        # else:
        #     self.markerAdd(nline, self.ARROW_MARKER_NUM)

        return

if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = PythonEditor()
    editor.show()
    editor.setText(open(sys.argv[0]).read())
    app.exec_()