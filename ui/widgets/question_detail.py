"""Question detail panel — streaming layout for MC/MS/fill/TF, tabs for short/coding."""

from typing import Optional

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
    QTextBrowser, QTextEdit, QPushButton, QLineEdit,
    QRadioButton, QCheckBox, QButtonGroup,
    QScrollArea, QSizePolicy, QMessageBox,
)

from models.question import Question
from .code_editor import CodeEditor
from .markdown_editor import MarkdownEditor
from .difficulty_badge import DifficultyBadge
from .status_indicator import StatusIndicator
from .tag_badge import TagBadge


class QuestionDetail(QWidget):
    """Center panel — streaming or tab layout depending on question type.

    Streaming (MC / MS / fill / TF):
        Description → Answer → Feedback + Explanation → Notes — all in one scroll.
        MC and TF auto-submit on selection (no submit button).

    Tabs (short_answer / coding):
        Tabbed layout with Description, Answer, Explanation, Reference, Notes.

    Signals:
        save_requested(Question)
        status_changed(str, str)
    """

    save_requested = Signal(object)
    status_changed = Signal(str, str)

    STREAMING_TYPES = {"multiple_choice", "multiple_select", "fill_in_blank", "true_false"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._question: Optional[Question] = None
        self._answer_widgets: dict = {}
        self._is_streaming = False
        self._auto_submit_timer = QTimer(self)
        self._auto_submit_timer.setSingleShot(True)
        self._auto_submit_timer.timeout.connect(self._on_submit_answer)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # ---- Placeholder ----
        self._placeholder = QLabel("← 选择一道题目开始练习")
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.setStyleSheet("font-size: 16px; color: #666; padding: 100px;")
        layout.addWidget(self._placeholder)

        # ---- Detail area ----
        self._detail_widget = QWidget()
        detail_layout = QVBoxLayout(self._detail_widget)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(8)

        # Title
        self._title_label = QLabel()
        self._title_label.setStyleSheet("font-size: 20px; font-weight: bold; padding: 4px 0;")
        self._title_label.setWordWrap(True)
        detail_layout.addWidget(self._title_label)

        # Metadata row
        meta_row = QHBoxLayout()
        self._type_label = QLabel()
        self._type_label.setStyleSheet(
            "font-size: 12px; background: #3c3c3c; border-radius: 4px; padding: 2px 8px;")
        meta_row.addWidget(self._type_label)
        self._difficulty_badge = DifficultyBadge()
        meta_row.addWidget(self._difficulty_badge)
        self._status_indicator = StatusIndicator()
        meta_row.addWidget(self._status_indicator)
        meta_row.addStretch()
        detail_layout.addLayout(meta_row)

        # Category + tags
        tag_row = QHBoxLayout()
        self._category_label = QLabel()
        self._category_label.setStyleSheet("font-size: 12px; color: #aaa;")
        tag_row.addWidget(self._category_label)
        self._tags_layout = QHBoxLayout()
        self._tags_layout.setSpacing(4)
        tag_row.addLayout(self._tags_layout)
        tag_row.addStretch()
        detail_layout.addLayout(tag_row)

        # ================================================================
        #  TABS layout (short_answer / coding)
        # ================================================================
        self._tabs = QTabWidget()

        self._desc_browser = QTextBrowser()
        self._desc_browser.setOpenExternalLinks(True)
        self._tabs.addTab(self._desc_browser, "📖 题目")

        self._answer_tab = QWidget()
        self._answer_layout = QVBoxLayout(self._answer_tab)
        self._answer_layout.setContentsMargins(12, 12, 12, 12)
        self._answer_layout.setSpacing(10)
        self._tabs.addTab(self._answer_tab, "✏️ 作答")

        self._explanation_browser = QTextBrowser()
        self._explanation_browser.setOpenExternalLinks(True)
        self._tabs.addTab(self._explanation_browser, "💡 解析")

        self._ref_solution_editor = CodeEditor(language="python", read_only=True)
        self._ref_solution_tab_idx = self._tabs.addTab(
            self._ref_solution_editor, "💻 参考解答")

        # Notes tab with Markdown editor
        self._notes_widget = QWidget()
        notes_tab_layout = QVBoxLayout(self._notes_widget)
        notes_tab_layout.setContentsMargins(4, 4, 4, 4)
        notes_tab_layout.setSpacing(6)
        self._notes_editor = MarkdownEditor()
        notes_tab_layout.addWidget(self._notes_editor)
        self._save_notes_btn = QPushButton("💾 保存笔记")
        self._save_notes_btn.setFixedHeight(28)
        self._save_notes_btn.clicked.connect(self._on_save)
        notes_tab_layout.addWidget(self._save_notes_btn)
        self._tabs.addTab(self._notes_widget, "📝 笔记")

        detail_layout.addWidget(self._tabs, stretch=1)

        # ================================================================
        #  STREAMING layout (MC / MS / fill / TF)
        # ================================================================
        self._stream_scroll = QScrollArea()
        self._stream_scroll.setWidgetResizable(True)
        self._stream_scroll.setFrameShape(QScrollArea.NoFrame)

        self._stream_widget = QWidget()
        self._stream_layout = QVBoxLayout(self._stream_widget)
        self._stream_layout.setContentsMargins(4, 4, 4, 4)
        self._stream_layout.setSpacing(10)

        # Description
        self._stream_desc = QTextBrowser()
        self._stream_desc.setOpenExternalLinks(True)
        self._stream_desc.setMinimumHeight(60)
        self._stream_desc.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self._stream_layout.addWidget(self._stream_desc)
        self._stream_layout.addWidget(self._make_sep())

        # Answer area
        self._stream_answer_label = QLabel("✏️ 作答")
        self._stream_answer_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self._stream_layout.addWidget(self._stream_answer_label)

        self._stream_answer_container = QWidget()
        self._stream_answer_layout = QVBoxLayout(self._stream_answer_container)
        self._stream_answer_layout.setContentsMargins(0, 0, 0, 0)
        self._stream_answer_layout.setSpacing(8)
        self._stream_layout.addWidget(self._stream_answer_container)

        # Feedback
        self._stream_feedback = QLabel("")
        self._stream_feedback.setAlignment(Qt.AlignCenter)
        self._stream_feedback.setWordWrap(True)
        self._stream_feedback.setStyleSheet(
            "font-size: 14px; padding: 10px 16px; border-radius: 6px;")
        self._stream_feedback.setVisible(False)
        self._stream_layout.addWidget(self._stream_feedback)

        # Explanation
        self._stream_expl_label = QLabel("💡 解析")
        self._stream_expl_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; padding-top: 8px;")
        self._stream_expl_label.setVisible(False)
        self._stream_layout.addWidget(self._stream_expl_label)

        self._stream_expl = QTextBrowser()
        self._stream_expl.setOpenExternalLinks(True)
        self._stream_expl.setMinimumHeight(40)
        self._stream_expl.setVisible(False)
        self._stream_layout.addWidget(self._stream_expl)

        # Notes section with Markdown editor + save button
        self._stream_layout.addWidget(self._make_sep())
        self._stream_layout.addWidget(
            QLabel("📝 笔记（支持 Markdown）"))
        self._stream_notes = MarkdownEditor()
        self._stream_notes.setMinimumHeight(120)
        self._stream_layout.addWidget(self._stream_notes)

        self._stream_save_btn = QPushButton("💾 保存笔记")
        self._stream_save_btn.setFixedHeight(28)
        self._stream_save_btn.clicked.connect(self._on_save)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(self._stream_save_btn)
        self._stream_layout.addLayout(btn_row)

        self._stream_layout.addStretch()
        self._stream_scroll.setWidget(self._stream_widget)
        detail_layout.addWidget(self._stream_scroll, stretch=1)

        # ================================================================
        #  Submit button (only for fill / short / coding)
        # ================================================================
        submit_row = QHBoxLayout()
        submit_row.addStretch()
        self._submit_btn = QPushButton("📤 提交答案")
        self._submit_btn.setFixedHeight(32)
        self._submit_btn.clicked.connect(self._on_submit_answer)
        self._submit_btn.setVisible(False)
        submit_row.addWidget(self._submit_btn)
        detail_layout.addLayout(submit_row)

        layout.addWidget(self._detail_widget)
        self._detail_widget.hide()
        self._show_tabs_mode()

    def _make_sep(self) -> QWidget:
        w = QWidget()
        w.setFixedHeight(1)
        w.setStyleSheet("background-color: #3c3c3c;")
        return w

    # ================================================================
    #  Layout mode switching
    # ================================================================

    def _show_streaming_mode(self):
        self._is_streaming = True
        self._tabs.hide()
        self._stream_scroll.show()

    def _show_tabs_mode(self):
        self._is_streaming = False
        self._stream_scroll.hide()
        self._tabs.show()

    # ================================================================
    #  Public API
    # ================================================================

    def load_question(self, question: Question, category_name: str = "",
                      tags: list = None):
        self._question = question
        self._auto_submit_timer.stop()
        self._placeholder.hide()
        self._detail_widget.show()

        self._title_label.setText(question.title)
        self._difficulty_badge.set_difficulty(question.difficulty)
        self._status_indicator.set_status(question.status)

        from config.constants import QuestionType
        qt = QuestionType.from_str(question.question_type)
        self._type_label.setText(qt.display_name())

        self._category_label.setText(f"📁 {category_name}" if category_name else "")

        self._clear_tags()
        if tags:
            for tag in tags:
                badge = TagBadge(tag.id, tag.name)
                self._tags_layout.addWidget(badge)
            self._tags_layout.addStretch()

        qtype = question.question_type
        use_streaming = qtype in self.STREAMING_TYPES

        # Reset submit button text
        self._submit_btn.setText("📤 提交答案")

        if use_streaming:
            self._show_streaming_mode()
            self._load_streaming(question)
        else:
            self._show_tabs_mode()
            self._load_tabs(question)

    def _load_streaming(self, question: Question):
        qtype = question.question_type

        # Description
        desc_html = question.description.replace("\n", "<br>")
        self._stream_desc.setHtml(desc_html)
        self._stream_desc.document().setDocumentMargin(6)
        self._stream_desc.setFixedHeight(
            max(80, int(self._stream_desc.document().size().height() + 12)))

        # Explanation
        expl_html = (question.explanation or "（暂无解析）").replace("\n", "<br>")
        self._stream_expl.setHtml(expl_html)

        # Notes
        self._stream_notes.setPlainText(question.notes or "")

        # Answer area
        self._clear_stream_answer()
        self._build_stream_answer(question)

        # Feedback visibility
        if question.status in ("correct", "incorrect"):
            self._show_stream_feedback(question)
            self._stream_expl_label.setVisible(True)
            self._stream_expl.setVisible(True)
        else:
            self._stream_feedback.setVisible(False)
            self._stream_expl_label.setVisible(False)
            self._stream_expl.setVisible(False)

        # Show submit button only for fill_in_blank
        self._submit_btn.setVisible(qtype == "fill_in_blank")

        self._stream_scroll.verticalScrollBar().setValue(0)

    def _load_tabs(self, question: Question):
        qtype = question.question_type

        desc_html = question.description.replace("\n", "<br>")
        self._desc_browser.setHtml(desc_html)

        expl_html = (question.explanation or "（暂无解析）").replace("\n", "<br>")
        self._explanation_browser.setHtml(expl_html)

        self._notes_editor.setPlainText(question.notes or "")

        self._build_tab_answer(question)

        if qtype == "coding":
            self._tabs.setTabVisible(self._ref_solution_tab_idx, True)
            self._ref_solution_editor.setPlainText(question.solution or "")
        else:
            self._tabs.setTabVisible(self._ref_solution_tab_idx, False)

        # Show submit button for short_answer and coding
        self._submit_btn.setVisible(
            qtype in ("short_answer", "coding"))

        if qtype == "coding":
            self._submit_btn.setText("💾 保存代码")

    def clear(self):
        self._question = None
        self._auto_submit_timer.stop()
        self._detail_widget.hide()
        self._placeholder.show()

    def get_current_question_id(self) -> Optional[str]:
        return self._question.id if self._question else None

    def get_current_question_type(self) -> str:
        return self._question.question_type if self._question else ""

    # ================================================================
    #  Answer builders — Streaming
    # ================================================================

    def _clear_stream_answer(self):
        self._clear_layout(self._stream_answer_layout)
        self._answer_widgets.clear()

    def _build_stream_answer(self, question: Question):
        qtype = question.question_type

        if qtype == "multiple_choice":
            self._build_mc_widgets(self._stream_answer_layout, question)
        elif qtype == "multiple_select":
            self._build_ms_widgets(self._stream_answer_layout, question)
        elif qtype == "true_false":
            self._build_tf_widgets(self._stream_answer_layout, question)
        elif qtype == "fill_in_blank":
            self._build_fill_widgets(self._stream_answer_layout, question)

        if question.user_answer:
            self._restore_user_answer(question)

        self._stream_answer_layout.addStretch()

    # ================================================================
    #  Answer builders — Tabs
    # ================================================================

    def _clear_tab_answer(self):
        self._clear_layout(self._answer_layout)
        self._answer_widgets.clear()

    def _build_tab_answer(self, question: Question):
        self._clear_tab_answer()
        qtype = question.question_type

        if qtype == "short_answer":
            self._build_short_widgets(self._answer_layout, question)
        elif qtype == "coding":
            self._build_coding_widgets(self._answer_layout, question)
        else:
            self._answer_layout.addWidget(QLabel("未知题型"))

        self._answer_layout.addStretch()

        if question.user_answer:
            self._restore_user_answer(question)

        self._tabs.setCurrentIndex(1)

    # ================================================================
    #  Widget builders
    # ================================================================

    def _build_mc_widgets(self, target, question: Question):
        label = QLabel("请选择一个选项：")
        label.setStyleSheet("font-size: 14px; font-weight: bold;")
        target.addWidget(label)

        self._mc_group = QButtonGroup(self)
        for choice in question.choices:
            rb = QRadioButton(f"{choice.get('label', '')}. {choice.get('text', '')}")
            rb.setStyleSheet(
                "QRadioButton { font-size: 14px; padding: 6px; }"
                "QRadioButton::indicator { width: 18px; height: 18px; }")
            rb.toggled.connect(self._on_mc_toggled)
            self._mc_group.addButton(rb)
            self._answer_widgets[choice.get("label", "")] = rb
            target.addWidget(rb)

    def _build_ms_widgets(self, target, question: Question):
        label = QLabel("请选择所有正确的选项：")
        label.setStyleSheet("font-size: 14px; font-weight: bold;")
        target.addWidget(label)

        self._ms_checks: dict[str, QCheckBox] = {}
        for choice in question.choices:
            cb = QCheckBox(f"{choice.get('label', '')}. {choice.get('text', '')}")
            cb.setStyleSheet(
                "QCheckBox { font-size: 14px; padding: 6px; }"
                "QCheckBox::indicator { width: 18px; height: 18px; }")
            self._ms_checks[choice.get("label", "")] = cb
            self._answer_widgets[choice.get("label", "")] = cb
            target.addWidget(cb)

        # Submit button for multi-select
        ms_btn = QPushButton("📤 提交答案")
        ms_btn.setFixedHeight(32)
        ms_btn.clicked.connect(self._on_submit_answer)
        target.addWidget(ms_btn)

    def _build_tf_widgets(self, target, question: Question):
        label = QLabel("请判断正误：")
        label.setStyleSheet("font-size: 14px; font-weight: bold;")
        target.addWidget(label)

        btn_row = QHBoxLayout()
        self._tf_group = QButtonGroup(self)

        true_btn = QPushButton("✅ 正确 (True)")
        true_btn.setCheckable(True)
        true_btn.setFixedHeight(40)
        true_btn.setStyleSheet(
            "QPushButton { font-size: 14px; border: 2px solid #4CAF50;"
            " border-radius: 8px; }"
            "QPushButton:checked { background-color: #4CAF50; color: white; }")
        true_btn.clicked.connect(lambda: self._on_tf_clicked())
        self._tf_group.addButton(true_btn)
        self._answer_widgets["True"] = true_btn
        btn_row.addWidget(true_btn)

        false_btn = QPushButton("❌ 错误 (False)")
        false_btn.setCheckable(True)
        false_btn.setFixedHeight(40)
        false_btn.setStyleSheet(
            "QPushButton { font-size: 14px; border: 2px solid #F44336;"
            " border-radius: 8px; }"
            "QPushButton:checked { background-color: #F44336; color: white; }")
        false_btn.clicked.connect(lambda: self._on_tf_clicked())
        self._tf_group.addButton(false_btn)
        self._answer_widgets["False"] = false_btn
        btn_row.addWidget(false_btn)

        target.addLayout(btn_row)

    def _build_fill_widgets(self, target, question: Question):
        label = QLabel("请在下方输入你的答案：")
        label.setStyleSheet("font-size: 14px; font-weight: bold;")
        target.addWidget(label)

        self._fill_input = QLineEdit()
        self._fill_input.setPlaceholderText("输入答案...")
        self._fill_input.setFixedHeight(36)
        self._fill_input.setStyleSheet("font-size: 14px; padding: 6px 10px;")
        self._answer_widgets["fill_input"] = self._fill_input
        target.addWidget(self._fill_input)

    def _build_short_widgets(self, target, question: Question):
        label = QLabel("请在下方输入你的答案（简答）：")
        label.setStyleSheet("font-size: 14px; font-weight: bold;")
        target.addWidget(label)

        self._short_input = QTextEdit()
        self._short_input.setPlaceholderText("输入你的答案...")
        self._short_input.setFixedHeight(120)
        self._short_input.setStyleSheet("font-size: 13px;")
        self._answer_widgets["short_input"] = self._short_input
        target.addWidget(self._short_input)

    def _build_coding_widgets(self, target, question: Question):
        label = QLabel(f"使用 {question.language or 'python'} 编写解答：")
        label.setStyleSheet("font-size: 14px; font-weight: bold;")
        target.addWidget(label)

        self._code_editor = CodeEditor(language=question.language or "python")
        self._code_editor.setMinimumHeight(200)
        self._answer_widgets["code_editor"] = self._code_editor
        target.addWidget(self._code_editor)

        self._submit_btn.setText("💾 保存代码")

    # ================================================================
    #  Auto-submit triggers (MC + TF)
    # ================================================================

    def _on_mc_toggled(self, checked: bool):
        if checked and self._question:
            self._auto_submit_timer.start(300)

    def _on_tf_clicked(self):
        if self._question:
            self._auto_submit_timer.start(300)

    # ================================================================
    #  Restore answer
    # ================================================================

    def _restore_user_answer(self, question: Question):
        qtype = question.question_type
        ua = question.user_answer

        if qtype == "multiple_choice" and ua in self._answer_widgets:
            self._answer_widgets[ua].setChecked(True)
        elif qtype == "multiple_select":
            selected = set(ua.split(","))
            for label, cb in self._answer_widgets.items():
                if isinstance(cb, QCheckBox):
                    cb.setChecked(label in selected)
        elif qtype == "true_false" and ua in self._answer_widgets:
            self._answer_widgets[ua].setChecked(True)
        elif qtype == "fill_in_blank" and "fill_input" in self._answer_widgets:
            self._answer_widgets["fill_input"].setText(ua)
        elif qtype == "short_answer" and "short_input" in self._answer_widgets:
            self._answer_widgets["short_input"].setPlainText(ua)
        elif qtype == "coding" and "code_editor" in self._answer_widgets:
            self._answer_widgets["code_editor"].setPlainText(
                question.code_submission or "")

    # ================================================================
    #  Submit / Feedback
    # ================================================================

    def _on_submit_answer(self):
        if not self._question:
            return

        qtype = self._question.question_type
        user_answer = self._get_user_answer(qtype)

        if not user_answer and qtype not in ("coding",):
            return  # silently skip if no selection

        if qtype == "coding":
            self._question.code_submission = user_answer
            self._question.status = "attempted"
            self._question.touch()
            self._status_indicator.set_status(self._question.status)
            self.save_requested.emit(self._question)
            self.status_changed.emit(self._question.id, self._question.status)
            self._show_stream_feedback_text("✅ 代码已保存", "#4CAF50")
            return

        # Auto-grade
        is_correct = self._question.check_answer(user_answer)
        self._status_indicator.set_status(self._question.status)
        self.save_requested.emit(self._question)
        self.status_changed.emit(self._question.id, self._question.status)

        # Show feedback
        if is_correct:
            self._show_stream_feedback_text("🎉 回答正确！", "#4CAF50")
        else:
            correct = self._question.correct_answer
            self._show_stream_feedback_text(
                f"❌ 回答错误。正确答案是：{correct}", "#F44336")

        # In streaming mode, reveal explanation
        if self._is_streaming:
            self._stream_expl_label.setVisible(True)
            self._stream_expl.setVisible(True)
            expl_html = (
                self._question.explanation
                or f"正确答案是：{self._question.correct_answer}"
            ).replace("\n", "<br>")
            self._stream_expl.setHtml(expl_html)

    def _get_user_answer(self, qtype: str) -> str:
        if qtype == "multiple_choice":
            checked = self._mc_group.checkedButton()
            if checked:
                return checked.text().split(".")[0].strip()
            return ""
        elif qtype == "multiple_select":
            selected = []
            for label, cb in self._answer_widgets.items():
                if isinstance(cb, QCheckBox) and cb.isChecked():
                    selected.append(label)
            return ",".join(sorted(selected))
        elif qtype == "true_false":
            checked = self._tf_group.checkedButton()
            if checked:
                return "True" if "正确" in checked.text() else "False"
            return ""
        elif qtype == "fill_in_blank":
            return self._answer_widgets.get(
                "fill_input", QLineEdit()).text().strip()
        elif qtype == "short_answer":
            w = self._answer_widgets.get("short_input")
            return w.toPlainText().strip() if w else ""
        elif qtype == "coding":
            w = self._answer_widgets.get("code_editor")
            return w.toPlainText() if w else ""
        return ""

    def _show_stream_feedback(self, question: Question):
        if question.status == "correct":
            self._show_stream_feedback_text("🎉 回答正确！", "#4CAF50")
        elif question.status == "incorrect":
            self._show_stream_feedback_text(
                f"❌ 回答错误。正确答案是：{question.correct_answer}", "#F44336")

    def _show_stream_feedback_text(self, text: str, bg_color: str):
        self._stream_feedback.setText(text)
        self._stream_feedback.setStyleSheet(
            f"font-size: 14px; padding: 10px 16px; border-radius: 6px; "
            f"background-color: {bg_color}; color: white;")
        self._stream_feedback.setVisible(True)

    # ================================================================
    #  Save notes
    # ================================================================

    def _on_save(self):
        if not self._question:
            return
        if self._is_streaming:
            self._question.notes = self._stream_notes.toPlainText()
        else:
            self._question.notes = self._notes_editor.toPlainText()
        self.save_requested.emit(self._question)

    # ================================================================
    #  Helpers
    # ================================================================

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _clear_tags(self):
        while self._tags_layout.count():
            item = self._tags_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
