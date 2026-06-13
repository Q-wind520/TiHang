"""Chat bubble widget for displaying a single message."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QTextBrowser,
    QSizePolicy,
    QWidget,
)


class ChatBubble(QFrame):
    """A chat message bubble — user (right-aligned, blue) or assistant (left, gray)."""

    def __init__(
        self,
        role: str,
        content: str,
        timestamp: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self._role = role
        is_user = role == "user"

        # Main layout
        outer = QHBoxLayout(self)
        outer.setContentsMargins(8, 4, 8, 4)

        # Bubble frame
        bubble = QFrame()
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(10, 6, 10, 6)
        bubble_layout.setSpacing(4)

        # Content — use QTextBrowser for markdown rendering
        self._content_widget = QTextBrowser()
        self._content_widget.setOpenExternalLinks(True)
        self._content_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._content_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self._content_widget.setFrameShape(QFrame.NoFrame)
        self._content_widget.document().setDocumentMargin(0)
        self._set_html(content)

        bubble_layout.addWidget(self._content_widget)

        # Timestamp
        if timestamp:
            ts_label = QLabel(timestamp[:19].replace("T", " "))
            ts_label.setStyleSheet("font-size: 10px; color: #888;")
            bubble_layout.addWidget(ts_label)

        if is_user:
            outer.addStretch()
            outer.addWidget(bubble)
            bubble.setStyleSheet(
                "QFrame { background-color: #1a73e8; border-radius: 10px; }"
                "QTextBrowser { background: transparent; color: white; border: none; }"
            )
            self._content_widget.setStyleSheet(
                "QTextBrowser { background: transparent; color: white; border: none; }"
            )
        else:
            outer.addWidget(bubble)
            outer.addStretch()
            bubble.setStyleSheet(
                "QFrame { background-color: #333333; border-radius: 10px; }"
                "QTextBrowser { background: transparent; color: #e0e0e0; border: none; }"
            )
            self._content_widget.setStyleSheet(
                "QTextBrowser { background: transparent; color: #e0e0e0; border: none; }"
            )

        bubble.setMaximumWidth(500)

    def _set_html(self, content: str) -> None:
        """Update the HTML content of the bubble."""
        html = content.replace("\n", "<br>") if content else "&nbsp;"
        self._content_widget.setHtml(html)
        self._content_widget.setFixedHeight(
            max(24, int(self._content_widget.document().size().height() + 4))
        )

    def set_content(self, content: str) -> None:
        """Update the text content of this bubble (for streaming updates)."""
        self._set_html(content)
