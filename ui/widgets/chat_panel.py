"""Chat panel — right sidebar for AI assistant conversation."""

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QScrollArea,
    QTextEdit,
    QPushButton,
    QFrame,
    QSizePolicy,
)

from .chat_bubble import ChatBubble


class ChatPanel(QWidget):
    """Right sidebar for AI chat.

    Signals:
        send_message(str, str)      — emits (message_text, mode).
        new_session()               — start a new chat session.
        clear_session()             — clear current chat.
        provider_changed(str)       — user changed provider.
        stop_generation()           — user wants to stop streaming.
    """

    send_message = Signal(str, str)
    new_session = Signal()
    clear_session = Signal()
    provider_changed = Signal(str)
    stop_generation = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Header
        header = QHBoxLayout()
        title = QLabel("🤖 AI 助手")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()

        self._provider_combo = QComboBox()
        self._provider_combo.addItem("OpenAI", "openai")
        self._provider_combo.addItem("Anthropic", "anthropic")
        self._provider_combo.addItem("DeepSeek", "deepseek")
        self._provider_combo.currentIndexChanged.connect(
            lambda: self.provider_changed.emit(self._provider_combo.currentData())
        )
        header.addWidget(self._provider_combo)
        layout.addLayout(header)

        # Mode selector
        self._mode_combo = QComboBox()
        self._current_question_type = ""
        self._populate_modes("")  # Default: all non-coding modes
        layout.addWidget(self._mode_combo)

        # Chat scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        self._chat_container = QWidget()
        self._chat_layout = QVBoxLayout(self._chat_container)
        self._chat_layout.setSpacing(8)
        self._chat_layout.addStretch()
        scroll.setWidget(self._chat_container)

        layout.addWidget(scroll, stretch=1)

        # Streaming indicator
        self._streaming_label = QLabel("")
        self._streaming_label.setStyleSheet(
            "font-size: 11px; color: #ffa726; font-style: italic;"
        )
        self._streaming_label.hide()
        layout.addWidget(self._streaming_label)

        # Input area
        self._input = QTextEdit()
        self._input.setPlaceholderText("输入消息... (Ctrl+Enter 发送)")
        self._input.setFixedHeight(70)
        layout.addWidget(self._input)

        # Buttons row
        btn_row = QHBoxLayout()

        send_btn = QPushButton("📤 发送")
        send_btn.setFixedHeight(30)
        send_btn.clicked.connect(self._on_send)
        btn_row.addWidget(send_btn)

        stop_btn = QPushButton("⏹ 停止")
        stop_btn.setFixedHeight(30)
        stop_btn.clicked.connect(self.stop_generation.emit)
        btn_row.addWidget(stop_btn)

        btn_row.addStretch()

        new_btn = QPushButton("新对话")
        new_btn.setFixedHeight(28)
        new_btn.clicked.connect(self.new_session.emit)
        btn_row.addWidget(new_btn)

        clear_btn = QPushButton("清屏")
        clear_btn.setFixedHeight(28)
        clear_btn.clicked.connect(self.clear_session.emit)
        btn_row.addWidget(clear_btn)

        layout.addLayout(btn_row)

        self.setMinimumWidth(250)
        self.setMaximumWidth(450)

        # Buffer for streaming
        self._stream_buffer = ""

    # ---- Public API ----

    def add_message(self, role: str, content: str, timestamp: str = ""):
        """Append a message bubble to the chat."""
        bubble = ChatBubble(role, content, timestamp)
        # Insert before the stretch
        self._chat_layout.insertWidget(self._chat_layout.count() - 1, bubble)

    def start_streaming(self):
        """Show streaming indicator and create a pending assistant bubble."""
        self._stream_buffer = ""
        self._streaming_label.setText("AI 正在回复...")
        self._streaming_label.show()
        # Create a placeholder bubble for streaming content
        self._stream_bubble = ChatBubble("assistant", "")
        self._chat_layout.insertWidget(
            self._chat_layout.count() - 1, self._stream_bubble
        )

    def append_stream_chunk(self, chunk: str):
        """Append a chunk to the currently streaming message."""
        self._stream_buffer += chunk
        # Update the existing streaming bubble in-place
        if hasattr(self, "_stream_bubble") and self._stream_bubble:
            self._stream_bubble.set_content(self._stream_buffer)

    def finish_streaming(self):
        """Finalize the streaming message."""
        self._streaming_label.hide()
        self._stream_buffer = ""

    def set_streaming_error(self, error_msg: str):
        """Show an error in the chat."""
        self._streaming_label.setText(f"❌ {error_msg}")
        self._streaming_label.setStyleSheet(
            "font-size: 11px; color: #ef5350; font-style: italic;"
        )
        self._streaming_label.show()

    def clear_messages(self):
        """Remove all message bubbles from the chat."""
        while self._chat_layout.count() > 1:  # keep the stretch
            item = self._chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def set_provider(self, provider_name: str):
        """Update the provider combo without emitting signal."""
        self._provider_combo.blockSignals(True)
        idx = self._provider_combo.findData(provider_name)
        if idx >= 0:
            self._provider_combo.setCurrentIndex(idx)
        self._provider_combo.blockSignals(False)

    def get_mode(self) -> str:
        return self._mode_combo.currentData()

    def update_modes_for_type(self, question_type: str) -> None:
        """Update the mode combo based on question type (show/hide code_review)."""
        if question_type == self._current_question_type:
            return
        self._current_question_type = question_type
        self._populate_modes(question_type)

    def _populate_modes(self, question_type: str) -> None:
        """Fill the mode combo with modes appropriate for the question type."""
        from llm.prompt_templates import PromptTemplates

        self._mode_combo.blockSignals(True)
        self._mode_combo.clear()
        modes = PromptTemplates.available_modes_for_type(question_type or "")
        for label, mode_id in modes:
            self._mode_combo.addItem(label, mode_id)
        self._mode_combo.blockSignals(False)

    # ---- Slots ----

    def _on_send(self):
        text = self._input.toPlainText().strip()
        if not text:
            return
        mode = self._mode_combo.currentData()
        self.send_message.emit(text, mode)
        self._input.clear()

    def keyPressEvent(self, event):
        # Ctrl+Enter to send
        if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
            self._on_send()
            return
        super().keyPressEvent(event)
