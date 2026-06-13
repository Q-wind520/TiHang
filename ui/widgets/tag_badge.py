"""Small colored tag chip widget."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QLabel, QHBoxLayout, QPushButton, QWidget


class TagBadge(QWidget):
    """A small rounded tag chip with optional close button."""

    remove_clicked = Signal(str)  # emits tag_id

    COLORS = [
        "#2196F3", "#4CAF50", "#FF9800", "#E91E63",
        "#9C27B0", "#00BCD4", "#FF5722", "#795548",
    ]

    def __init__(
        self,
        tag_id: str,
        text: str,
        parent=None,
        removable: bool = False,
    ):
        super().__init__(parent)
        self.tag_id = tag_id
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(4)

        self.label = QLabel(text)
        self.label.setFont(QFont("Segoe UI", 9))

        layout.addWidget(self.label)

        if removable:
            btn = QPushButton("×")
            btn.setFixedSize(16, 16)
            btn.setStyleSheet(
                "QPushButton { border: none; color: white; "
                "font-weight: bold; padding: 0; }"
                "QPushButton:hover { color: #ff5252; }"
            )
            btn.clicked.connect(lambda: self.remove_clicked.emit(self.tag_id))
            layout.addWidget(btn)

        # Color based on tag name hash
        color = self._pick_color(text)
        self.setStyleSheet(
            f"TagBadge {{ background-color: {color}; border-radius: 8px; }}"
            f"QLabel {{ color: white; }}"
        )

    @staticmethod
    def _pick_color(text: str) -> str:
        idx = hash(text) % len(TagBadge.COLORS)
        return TagBadge.COLORS[idx]
