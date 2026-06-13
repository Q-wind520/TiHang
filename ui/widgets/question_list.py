"""Question list panel — left sidebar with search, filters, and rich card items."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QComboBox,
    QLabel,
    QPushButton,
    QFrame,
    QScrollArea,
)

from .question_list_item import QuestionListItem


class QuestionList(QWidget):
    """Left sidebar showing the question list with filters and rich card items.

    Signals:
        question_selected(str) — emits question_id when a row is clicked.
        filter_changed()        — emitted when a filter value changes.
        new_question()          — emitted when the "New" button is clicked.
        bank_changed(str)       — emits bank_id when bank selector changes.
        manage_banks()          — emitted to open bank management dialog.
    """

    question_selected = Signal(str)
    filter_changed = Signal()
    new_question = Signal()
    bank_changed = Signal(str)
    manage_banks = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_id: str | None = None
        self._item_widgets: dict[str, QuestionListItem] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ---- Header panel ----
        header_frame = QFrame()
        header_frame.setObjectName("ListHeader")
        header = QVBoxLayout(header_frame)
        header.setContentsMargins(10, 10, 10, 8)
        header.setSpacing(8)

        # Title row
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(8)

        title_label = QLabel("题目列表")
        title_label.setObjectName("ListTitle")
        title_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #e0e0e0; border: none; background: transparent;"
        )
        title_row.addWidget(title_label)
        title_row.addStretch()

        new_btn = QPushButton("＋ 新建")
        new_btn.setObjectName("NewQuestionBtn")
        new_btn.setFixedSize(64, 26)
        new_btn.setStyleSheet(
            "QPushButton#NewQuestionBtn {"
            "  background-color: #0e639c; color: white; border: none;"
            "  border-radius: 4px; font-size: 11px; font-weight: bold; padding: 2px 8px;"
            "}"
            "QPushButton#NewQuestionBtn:hover { background-color: #1177bb; }"
        )
        new_btn.clicked.connect(self.new_question.emit)
        title_row.addWidget(new_btn)

        header.addLayout(title_row)

        # Bank selector row
        bank_row = QHBoxLayout()
        bank_row.setContentsMargins(0, 0, 0, 0)
        bank_row.setSpacing(6)

        self._bank_combo = QComboBox()
        self._bank_combo.setObjectName("BankCombo")
        self._bank_combo.setStyleSheet(
            "QComboBox#BankCombo {"
            "  background-color: #2d2d2d; color: #d4d4d4; border: 1px solid #444;"
            "  border-radius: 4px; padding: 3px 8px; font-size: 12px;"
            "}"
            "QComboBox#BankCombo:hover { border-color: #007acc; }"
            "QComboBox#BankCombo::drop-down { border: none; width: 20px; }"
            "QComboBox#BankCombo QAbstractItemView {"
            "  background-color: #2d2d2d; color: #d4d4d4; selection-background-color: #094771;"
            "  border: 1px solid #555;"
            "}"
        )
        self._bank_combo.currentIndexChanged.connect(self._on_bank_changed)
        bank_row.addWidget(self._bank_combo, stretch=1)

        manage_btn = QPushButton("管理")
        manage_btn.setObjectName("ManageBankBtn")
        manage_btn.setFixedSize(40, 24)
        manage_btn.setStyleSheet(
            "QPushButton#ManageBankBtn {"
            "  background-color: transparent; color: #888; border: 1px solid #555;"
            "  border-radius: 4px; font-size: 10px; padding: 2px 4px;"
            "}"
            "QPushButton#ManageBankBtn:hover { color: #d4d4d4; border-color: #007acc; }"
        )
        manage_btn.clicked.connect(self.manage_banks.emit)
        bank_row.addWidget(manage_btn)

        header.addLayout(bank_row)

        # Search bar
        self._search = QLineEdit()
        self._search.setObjectName("SearchInput")
        self._search.setPlaceholderText("🔍 搜索题目...")
        self._search.setStyleSheet(
            "QLineEdit#SearchInput {"
            "  background-color: #2d2d2d; color: #d4d4d4; border: 1px solid #444;"
            "  border-radius: 6px; padding: 5px 10px; font-size: 12px;"
            "}"
            "QLineEdit#SearchInput:focus { border-color: #007acc; }"
        )
        self._search.textChanged.connect(self._on_filter_changed)
        header.addWidget(self._search)

        # Filter row — compact pills
        filter_row = QHBoxLayout()
        filter_row.setContentsMargins(0, 0, 0, 0)
        filter_row.setSpacing(6)

        self._type_filter = self._make_filter_combo("TypeFilter")
        self._type_filter.addItem("全部题型", "")
        self._type_filter.addItem("🔤 单选", "multiple_choice")
        self._type_filter.addItem("☑️ 多选", "multiple_select")
        self._type_filter.addItem("📝 填空", "fill_in_blank")
        self._type_filter.addItem("📄 简答", "short_answer")
        self._type_filter.addItem("✅ 判断", "true_false")
        self._type_filter.addItem("💻 编程", "coding")
        self._type_filter.currentIndexChanged.connect(self._on_filter_changed)
        filter_row.addWidget(self._type_filter)

        self._difficulty_filter = self._make_filter_combo("DiffFilter")
        self._difficulty_filter.addItem("全部难度", "")
        self._difficulty_filter.addItem("🟢 简单", "easy")
        self._difficulty_filter.addItem("🟠 中等", "medium")
        self._difficulty_filter.addItem("🔴 困难", "hard")
        self._difficulty_filter.currentIndexChanged.connect(self._on_filter_changed)
        filter_row.addWidget(self._difficulty_filter)

        self._status_filter = self._make_filter_combo("StatusFilter")
        self._status_filter.addItem("全部状态", "")
        self._status_filter.addItem("⬜ 未答", "unanswered")
        self._status_filter.addItem("✅ 正确", "correct")
        self._status_filter.addItem("❌ 错误", "incorrect")
        self._status_filter.addItem("🟡 尝试中", "attempted")
        self._status_filter.currentIndexChanged.connect(self._on_filter_changed)
        filter_row.addWidget(self._status_filter)

        header.addLayout(filter_row)

        layout.addWidget(header_frame)

        # ---- Separator ----
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #333; border: none; border-top: 1px solid #333;")
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        # ---- Question list ----
        self._list = QListWidget()
        self._list.setObjectName("QuestionListWidget")
        self._list.setSelectionMode(QListWidget.NoSelection)
        self._list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._list.setSpacing(2)
        self._list.itemClicked.connect(self._on_list_item_clicked)
        self._list.setStyleSheet(
            "QListWidget#QuestionListWidget {"
            "  background-color: #1e1e1e; border: none; outline: none;"
            "  padding: 4px 6px;"
            "}"
        )
        layout.addWidget(self._list, stretch=1)

        # ---- Stats footer ----
        footer_frame = QFrame()
        footer_frame.setObjectName("ListFooter")
        footer_frame.setFixedHeight(28)
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(10, 0, 10, 0)
        footer_layout.setSpacing(8)

        self._stats_label = QLabel("共 0 题")
        self._stats_label.setStyleSheet(
            "font-size: 11px; color: #888; border: none; background: transparent;"
        )
        footer_layout.addWidget(self._stats_label)
        footer_layout.addStretch()

        layout.addWidget(footer_frame)

        self.setMinimumWidth(240)
        self.setMaximumWidth(380)

    # ------------------------------------------------------------------
    #  Filter combo factory
    # ------------------------------------------------------------------

    @staticmethod
    def _make_filter_combo(name: str) -> QComboBox:
        """Create a compact filter combo with consistent styling."""
        combo = QComboBox()
        combo.setObjectName(name)
        combo.setStyleSheet(
            f"QComboBox#{name} {{"
            "  background-color: #2d2d2d; color: #aaa; border: 1px solid #3c3c3c;"
            "  border-radius: 4px; padding: 2px 6px; font-size: 11px; min-width: 70px;"
            "}"
            f"QComboBox#{name}:hover {{ border-color: #007acc; color: #d4d4d4; }}"
            f"QComboBox#{name}::drop-down {{ border: none; width: 16px; }}"
            f"QComboBox#{name} QAbstractItemView {{"
            "  background-color: #2d2d2d; color: #d4d4d4;"
            "  selection-background-color: #094771; border: 1px solid #555;"
            "}"
        )
        return combo

    # ---- Public API ----

    def get_filters(self) -> dict:
        return {
            "bank_id": self._bank_combo.currentData(),
            "search": self._search.text(),
            "question_type": self._type_filter.currentData(),
            "difficulty": self._difficulty_filter.currentData(),
            "status": self._status_filter.currentData(),
        }

    def load_banks(self, banks: list, current_bank_id: str = "") -> None:
        """Populate the bank selector combo."""
        self._bank_combo.blockSignals(True)
        self._bank_combo.clear()
        for bank in banks:
            self._bank_combo.addItem(f"📚 {bank.name}", bank.id)
        if current_bank_id:
            idx = self._bank_combo.findData(current_bank_id)
            if idx >= 0:
                self._bank_combo.setCurrentIndex(idx)
        self._bank_combo.blockSignals(False)

    def load_questions(self, questions: list) -> None:
        """Refresh the list with rich card items from Question objects."""
        self._list.clear()
        self._item_widgets.clear()

        for q in questions:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, q.id)
            card = QuestionListItem(q)
            self._item_widgets[q.id] = card

            # Size the item to match the card
            item.setSizeHint(card.sizeHint())
            self._list.addItem(item)
            self._list.setItemWidget(item, card)

            if q.id == self._selected_id:
                card.set_selected_style(True)
                card.setProperty("selected", True)

    def update_stats(self, counts: dict[str, int]) -> None:
        """Update the footer stats bar."""
        total = counts.get("total", 0)
        correct = counts.get("correct", 0)
        incorrect = counts.get("incorrect", 0)
        unanswered = counts.get("unanswered", 0)
        attempted = counts.get("attempted", 0)

        parts = [f"共 {total} 题"]
        if correct:
            parts.append(f"✅ {correct}")
        if incorrect:
            parts.append(f"❌ {incorrect}")
        if unanswered:
            parts.append(f"⬜ {unanswered}")
        if attempted:
            parts.append(f"🟡 {attempted}")

        self._stats_label.setText("  ·  ".join(parts))

    def select_question(self, question_id: str) -> None:
        """Highlight the given question in the list."""
        # Deselect previous
        if self._selected_id and self._selected_id in self._item_widgets:
            self._item_widgets[self._selected_id].set_selected_style(False)
            self._item_widgets[self._selected_id].setProperty("selected", False)

        self._selected_id = question_id

        # Select new
        if question_id and question_id in self._item_widgets:
            self._item_widgets[question_id].set_selected_style(True)
            self._item_widgets[question_id].setProperty("selected", True)
            # Scroll to the item
            for i in range(self._list.count()):
                item = self._list.item(i)
                if item.data(Qt.UserRole) == question_id:
                    self._list.scrollToItem(item, QListWidget.PositionAtCenter)
                    break

    # ------------------------------------------------------------------
    #  Slots
    # ------------------------------------------------------------------

    def _on_list_item_clicked(self, item: QListWidgetItem):
        """Handle click on a question card in the list."""
        qid = item.data(Qt.UserRole)
        if qid:
            self.question_selected.emit(qid)

    def _on_bank_changed(self, _index: int):
        bank_id = self._bank_combo.currentData()
        if bank_id:
            self.bank_changed.emit(bank_id)
            self.filter_changed.emit()

    def _on_filter_changed(self, *_args):
        self.filter_changed.emit()
