"""Color-coded difficulty label."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel


class DifficultyBadge(QLabel):
    """A colored label indicating problem difficulty."""

    COLORS = {
        "easy": ("#4CAF50", "#1B5E20"),       # green
        "medium": ("#FF9800", "#E65100"),     # orange
        "hard": ("#F44336", "#B71C1C"),       # red
    }

    def __init__(self, difficulty: str = "easy", parent=None):
        super().__init__(parent)
        self.set_difficulty(difficulty)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(22)

    def set_difficulty(self, difficulty: str):
        bg, text_color = self.COLORS.get(
            difficulty.lower(), ("#9E9E9E", "#424242")
        )
        label = difficulty.capitalize() if difficulty else "Unknown"
        self.setText(label)
        self.setStyleSheet(
            f"DifficultyBadge {{ "
            f"background-color: {bg}; "
            f"color: white; "
            f"border-radius: 4px; "
            f"padding: 2px 10px; "
            f"font-size: 11px; "
            f"font-weight: bold; }}"
        )
