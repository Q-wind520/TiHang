"""Question list item — a rich card widget for the question list sidebar."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QWidget,
    QSizePolicy,
)

from config.constants import QuestionType, Difficulty, QuestionStatus


class QuestionListItem(QFrame):
    """A card-style list item displaying question metadata at a glance.

    Visual structure:
    ┌─────────────────────────────────┐
    │ ○ 题目标题                       │
    │   题型徽章  难度徽章              │
    └─────────────────────────────────┘
    """

    # Difficulty → left-strip color
    DIFFICULTY_COLORS = {
        "easy": "#4CAF50",
        "medium": "#FF9800",
        "hard": "#F44336",
    }

    # Question type → short display name + icon
    TYPE_META = {
        "multiple_choice": ("🔤", "单选"),
        "multiple_select": ("☑️", "多选"),
        "fill_in_blank": ("📝", "填空"),
        "short_answer": ("📄", "简答"),
        "true_false": ("✅", "判断"),
        "coding": ("💻", "编程"),
    }

    # Status → dot color + label
    STATUS_COLORS = {
        "unanswered": ("#9E9E9E", "未答"),
        "correct": ("#4CAF50", "正确"),
        "incorrect": ("#F44336", "错误"),
        "unsolved": ("#9E9E9E", "未解决"),
        "attempted": ("#FF9800", "尝试中"),
        "solved": ("#4CAF50", "已解决"),
    }

    _DEFAULT_STATUS = ("#9E9E9E", "未知")
    _DEFAULT_DIFFICULTY = "#9E9E9E"
    _DEFAULT_TYPE = ("", "未知")

    def __init__(self, question, parent=None):
        super().__init__(parent)
        self._question_id = question.id
        self.setObjectName("QuestionListItem")
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(52)
        self.setMaximumHeight(68)

        diff_color = self.DIFFICULTY_COLORS.get(
            question.difficulty, self._DEFAULT_DIFFICULTY
        )

        # ---- Main content ----
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(10, 4, 8, 4)
        content_layout.setSpacing(2)

        # Top row: status dot + title
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(6)

        # Status dot
        status_color, status_text = self.STATUS_COLORS.get(
            question.status, self._DEFAULT_STATUS
        )
        self._status_dot = QLabel()
        self._status_dot.setFixedSize(8, 8)
        self._status_dot.setStyleSheet(
            f"background-color: {status_color}; border-radius: 4px; border: none;"
        )
        self._status_dot.setToolTip(status_text)
        title_row.addWidget(self._status_dot, alignment=Qt.AlignVCenter)

        # Title
        self._title_label = QLabel(question.title or "（无标题）")
        self._title_label.setObjectName("ItemTitle")
        self._title_label.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: #d4d4d4; border: none; background: transparent;"
        )
        self._title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._title_label.setWordWrap(False)
        title_row.addWidget(self._title_label, stretch=1)

        content_layout.addLayout(title_row)

        # Bottom row: type badge + difficulty badge
        badge_row = QHBoxLayout()
        badge_row.setContentsMargins(14, 0, 0, 0)  # indent aligns with title after dot
        badge_row.setSpacing(6)

        _, type_name = self.TYPE_META.get(
            question.question_type, self._DEFAULT_TYPE
        )
        self._type_badge = self._make_badge(
            type_name,
            bg="#3a3a3a",
            fg="#cccccc",
        )
        badge_row.addWidget(self._type_badge)

        diff_name = {"easy": "简单", "medium": "中等", "hard": "困难"}.get(
            question.difficulty, question.difficulty
        )
        self._diff_badge = self._make_badge(
            diff_name,
            bg=f"{diff_color}22",  # very transparent
            fg=diff_color,
        )
        badge_row.addWidget(self._diff_badge)

        badge_row.addStretch()
        content_layout.addLayout(badge_row)

        # ---- Assemble ----
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(content, stretch=1)

    # ------------------------------------------------------------------
    #  Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_badge(text: str, bg: str, fg: str) -> QLabel:
        """Create a small rounded badge label."""
        label = QLabel(text)
        label.setStyleSheet(
            f"background-color: {bg}; color: {fg}; "
            f"border-radius: 6px; padding: 1px 8px; "
            f"font-size: 10px; border: none;"
        )
        label.setFixedHeight(20)
        label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        return label

    # ------------------------------------------------------------------
    #  Public
    # ------------------------------------------------------------------

    @property
    def question_id(self) -> str:
        return self._question_id

    def set_selected_style(self, selected: bool) -> None:
        """Update appearance to reflect selection state."""
        if selected:
            self.setStyleSheet(
                "#QuestionListItem { background-color: #094771; border-radius: 6px; }"
            )
        else:
            self.setStyleSheet(
                "#QuestionListItem { background-color: transparent; border-radius: 6px; }"
            )

    def enterEvent(self, event):
        """Hover highlight."""
        if not self.property("selected"):
            self.setStyleSheet(
                "#QuestionListItem { background-color: #2a2d2e; border-radius: 6px; }"
            )
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Restore default style."""
        if not self.property("selected"):
            self.setStyleSheet(
                "#QuestionListItem { background-color: transparent; border-radius: 6px; }"
            )
        super().leaveEvent(event)
