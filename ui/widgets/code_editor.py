"""Code editor widget with line numbers and syntax highlighting."""

from PySide6.QtCore import Qt, QRect, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QTextFormat,
    QKeyEvent,
)
from PySide6.QtWidgets import (
    QPlainTextEdit,
    QWidget,
    QTextEdit,
)

from .syntax_highlighter import PygmentsHighlighter


class LineNumberArea(QWidget):
    """Widget that paints line numbers beside the editor."""

    def __init__(self, editor: "CodeEditor"):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self):
        return self._editor._line_number_area_size()

    def paintEvent(self, event):
        self._editor._paint_line_numbers(event)


class CodeEditor(QPlainTextEdit):
    """A code editor with line numbers, syntax highlighting, and tab handling.

    Signals:
        code_changed() — emitted when the text content changes.
    """

    code_changed = Signal()

    def __init__(
        self,
        parent=None,
        theme: str = "monokai",
        language: str = "python",
        read_only: bool = False,
    ):
        super().__init__(parent)
        self._line_number_area = LineNumberArea(self)
        self._highlighter = PygmentsHighlighter(self.document(), theme, language)

        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._highlight_current_line)
        self.textChanged.connect(self._on_text_changed)

        self._update_line_number_area_width(0)
        self._highlight_current_line()
        self._apply_theme(theme)
        self.setReadOnly(read_only)

        # Tab handling
        self.setTabStopDistance(32)  # 4 spaces worth

        # Font
        font = QFont("Consolas", 13)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)

    def set_theme(self, theme: str) -> None:
        self._highlighter.set_theme(theme)
        self._apply_theme(theme)

    def set_language(self, language: str) -> None:
        self._highlighter.set_language(language)

    def set_editor_font(self, family: str, size: int) -> None:
        font = QFont(family, size)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)

    def set_tab_width(self, spaces: int) -> None:
        font_width = self.fontMetrics().horizontalAdvance(" ")
        self.setTabStopDistance(font_width * spaces if font_width > 0 else spaces * 8)

    def _on_text_changed(self) -> None:
        self.code_changed.emit()

    # ---- Line number area ----

    def _line_number_area_size(self):
        digits = max(1, len(str(self.blockCount())))
        space = 10 + self.fontMetrics().horizontalAdvance("9") * (digits + 1)
        return QRect(0, 0, space, 0).size()

    def _update_line_number_area_width(self, _new_block_count: int):
        self.setViewportMargins(
            self._line_number_area.sizeHint().width(), 0, 0, 0
        )

    def _update_line_number_area(self, rect: QRect, dy: int):
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(
                0, rect.y(), self._line_number_area.width(), rect.height()
            )
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(
            QRect(
                cr.left(),
                cr.top(),
                self._line_number_area.sizeHint().width(),
                cr.height(),
            )
        )

    def _paint_line_numbers(self, event):
        painter = QPainter(self._line_number_area)
        painter.fillRect(event.rect(), QColor("#1e1e1e"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(
            self.blockBoundingGeometry(block)
            .translated(self.contentOffset())
            .top()
        )
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#858585"))
                painter.drawText(
                    0,
                    top,
                    self._line_number_area.width()
                    - self.fontMetrics().horizontalAdvance("9"),
                    self.fontMetrics().height(),
                    Qt.AlignRight,
                    number,
                )
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def _highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor("#2a2a2a"))
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def _apply_theme(self, theme: str) -> None:
        from config.defaults import PYGMENTS_THEMES

        theme_info = PYGMENTS_THEMES.get(theme, PYGMENTS_THEMES["monokai"])
        bg = QColor(theme_info["background"])
        text_color = QColor(theme_info["text"])
        self.setStyleSheet(
            f"QPlainTextEdit {{ background-color: {bg.name()}; "
            f"color: {text_color.name()}; "
            f"border: 1px solid #3c3c3c; }}"
        )

    def keyPressEvent(self, event: QKeyEvent):
        # Tab inserts spaces instead of changing focus
        if event.key() == Qt.Key_Tab:
            self.insertPlainText("    ")
            return
        super().keyPressEvent(event)
