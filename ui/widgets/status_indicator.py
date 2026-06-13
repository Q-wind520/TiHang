"""Question status indicator (colored dot + label)."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QHBoxLayout, QWidget


class StatusIndicator(QWidget):
    """A colored dot + text label showing question status."""

    COLORS = {
        "unanswered": ("#9E9E9E", "未答"),
        "correct": ("#4CAF50", "正确"),
        "incorrect": ("#F44336", "错误"),
        # Coding-specific
        "unsolved": ("#9E9E9E", "未解决"),
        "attempted": ("#FF9800", "尝试中"),
        "solved": ("#4CAF50", "已解决"),
    }

    def __init__(self, status: str = "unanswered", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._dot = QLabel()
        self._dot.setFixedSize(10, 10)

        self._label = QLabel()
        self._label.setStyleSheet("font-size: 12px;")

        layout.addWidget(self._dot)
        layout.addWidget(self._label)
        layout.addStretch()

        self.set_status(status)

    def set_status(self, status: str):
        color, text = self.COLORS.get(status, ("#9E9E9E", status))
        self._dot.setStyleSheet(
            f"QLabel {{ background-color: {color}; border-radius: 5px; }}"
        )
        self._label.setText(text)
