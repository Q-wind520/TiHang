"""Dialog for creating or editing a question — type-aware dynamic form."""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QPushButton,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QStackedWidget,
    QWidget,
    QSpinBox,
)

from models.question import Question
from models.category import Category
from models.tag import Tag


class QuestionDialog(QDialog):
    """Modal dialog for creating or editing a question with type-specific fields."""

    QUESTION_TYPES = [
        ("单选题 (Single Choice)", "multiple_choice"),
        ("多选题 (Multiple Select)", "multiple_select"),
        ("填空题 (Fill in Blank)", "fill_in_blank"),
        ("简答题 (Short Answer)", "short_answer"),
        ("判断题 (True/False)", "true_false"),
        ("编程题 (Coding)", "coding"),
    ]

    def __init__(
        self,
        parent=None,
        question: Optional[Question] = None,
        categories: Optional[list[Category]] = None,
        tags: Optional[list[Tag]] = None,
        question_tags: Optional[list[Tag]] = None,
    ):
        super().__init__(parent)
        self._question = question
        self._categories = categories or []
        self._tags = tags or []

        if question:
            self.setWindowTitle(f"编辑题目 — {question.title}")
        else:
            self.setWindowTitle("新建题目")

        self.setMinimumSize(620, 550)

        layout = QVBoxLayout(self)

        # ---- Type selector ----
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("题型:"))
        self._type_combo = QComboBox()
        for label, type_id in self.QUESTION_TYPES:
            self._type_combo.addItem(label, type_id)
        self._type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_row.addWidget(self._type_combo)
        type_row.addStretch()
        layout.addLayout(type_row)

        # ---- Common fields ----
        form = QFormLayout()
        form.setSpacing(8)

        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("输入题目名称...")
        form.addRow("标题:", self._title_edit)

        self._desc_edit = QTextEdit()
        self._desc_edit.setPlaceholderText("输入题目描述（支持 Markdown）...")
        self._desc_edit.setMinimumHeight(100)
        form.addRow("描述:", self._desc_edit)

        self._difficulty_combo = QComboBox()
        self._difficulty_combo.addItems(["easy", "medium", "hard"])
        form.addRow("难度:", self._difficulty_combo)

        layout.addLayout(form)

        # ---- Type-specific fields (QStackedWidget) ----
        layout.addWidget(QLabel("题型特定设置:"))
        self._type_stack = QStackedWidget()

        # Page 0: Single Choice
        self._mc_page = self._create_mc_page()
        self._type_stack.addWidget(self._mc_page)

        # Page 1: Multiple Select
        self._ms_page = self._create_ms_page()
        self._type_stack.addWidget(self._ms_page)

        # Page 2: Fill in Blank
        self._fill_page = self._create_fill_page()
        self._type_stack.addWidget(self._fill_page)

        # Page 2: Short Answer
        self._short_page = self._create_short_page()
        self._type_stack.addWidget(self._short_page)

        # Page 3: True/False
        self._tf_page = self._create_tf_page()
        self._type_stack.addWidget(self._tf_page)

        # Page 4: Coding
        self._coding_page = self._create_coding_page()
        self._type_stack.addWidget(self._coding_page)

        layout.addWidget(self._type_stack)

        # ---- Explanation ----
        layout.addWidget(QLabel("题目解析:"))
        self._explanation_edit = QTextEdit()
        self._explanation_edit.setPlaceholderText("输入答案解析（可选）...")
        self._explanation_edit.setMinimumHeight(60)
        layout.addWidget(self._explanation_edit)

        # ---- Category + Tags ----
        cat_row = QHBoxLayout()
        self._category_combo = QComboBox()
        self._category_combo.addItem("（无分类）", "")
        for cat in self._categories:
            self._category_combo.addItem(cat.name, cat.id)
        cat_row.addWidget(QLabel("分类:"))
        cat_row.addWidget(self._category_combo)
        cat_row.addStretch()
        layout.addLayout(cat_row)

        layout.addWidget(QLabel("标签（勾选适用标签）:"))
        self._tag_list = QListWidget()
        self._tag_list.setMaximumHeight(100)
        for tag in self._tags:
            item = QListWidgetItem(tag.name)
            item.setData(Qt.UserRole, tag.id)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self._tag_list.addItem(item)
        layout.addWidget(self._tag_list)

        # ---- Source URL ----
        url_row = QHBoxLayout()
        self._url_edit = QLineEdit()
        self._url_edit.setPlaceholderText("题目来源 URL（可选）...")
        url_row.addWidget(QLabel("来源:"))
        url_row.addWidget(self._url_edit)
        layout.addLayout(url_row)

        # ---- Buttons ----
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Populate if editing
        if question:
            self._populate_from_question(question, question_tags)

    # ================================================================
    #  Type-specific pages
    # ================================================================

    def _create_mc_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 4)

        # 4 option inputs
        self._mc_options: list[tuple[QLineEdit, QLineEdit]] = []
        labels = ["A", "B", "C", "D"]
        for lbl in labels:
            row = QHBoxLayout()
            row.addWidget(QLabel(f"选项 {lbl}:"))
            text_edit = QLineEdit()
            text_edit.setPlaceholderText(f"选项 {lbl} 的内容...")
            row.addWidget(text_edit)
            self._mc_options.append((QLabel(lbl), text_edit))
            layout.addLayout(row)

        # Correct answer
        ans_row = QHBoxLayout()
        ans_row.addWidget(QLabel("正确答案:"))
        self._mc_correct = QComboBox()
        self._mc_correct.addItems(["A", "B", "C", "D"])
        ans_row.addWidget(self._mc_correct)
        ans_row.addStretch()
        layout.addLayout(ans_row)

        return page

    def _create_ms_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 4)

        self._ms_options: list[tuple[QLabel, QLineEdit]] = []
        labels = ["A", "B", "C", "D", "E", "F"]
        for lbl in labels:
            row = QHBoxLayout()
            row.addWidget(QLabel(f"选项 {lbl}:"))
            text_edit = QLineEdit()
            text_edit.setPlaceholderText(f"选项 {lbl} 的内容...")
            row.addWidget(text_edit)
            self._ms_options.append((QLabel(lbl), text_edit))
            layout.addLayout(row)

        ans_row = QHBoxLayout()
        ans_row.addWidget(QLabel("正确答案（可多选）:"))
        self._ms_correct_checks: list[tuple[str, object]] = []
        for lbl in labels:
            from PySide6.QtWidgets import QCheckBox
            cb = QCheckBox(lbl)
            self._ms_correct_checks.append((lbl, cb))
            ans_row.addWidget(cb)
        ans_row.addStretch()
        layout.addLayout(ans_row)

        return page

    def _create_fill_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 4)

        layout.addWidget(QLabel("提示：在题目描述中用 ___ 或 **___ 标记填空位置"))

        ans_row = QHBoxLayout()
        ans_row.addWidget(QLabel("正确答案:"))
        self._fill_correct = QLineEdit()
        self._fill_correct.setPlaceholderText("输入填空的正确答案...")
        ans_row.addWidget(self._fill_correct)
        layout.addLayout(ans_row)

        return page

    def _create_short_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 4)

        layout.addWidget(QLabel("参考答案/评分要点:"))
        self._short_correct = QTextEdit()
        self._short_correct.setPlaceholderText("输入参考答案或关键要点...")
        self._short_correct.setMinimumHeight(80)
        layout.addWidget(self._short_correct)

        return page

    def _create_tf_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 4)

        ans_row = QHBoxLayout()
        ans_row.addWidget(QLabel("正确答案:"))
        self._tf_correct = QComboBox()
        self._tf_correct.addItem("正确 (True)", "True")
        self._tf_correct.addItem("错误 (False)", "False")
        ans_row.addWidget(self._tf_correct)
        ans_row.addStretch()
        layout.addLayout(ans_row)

        return page

    def _create_coding_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 4)

        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel("编程语言:"))
        self._coding_language = QComboBox()
        self._coding_language.addItems(
            ["python", "java", "cpp", "javascript", "go", "rust", "other"]
        )
        lang_row.addWidget(self._coding_language)
        lang_row.addStretch()
        layout.addLayout(lang_row)

        layout.addWidget(QLabel("参考解答:"))
        self._coding_solution = QTextEdit()
        self._coding_solution.setPlaceholderText("输入参考解答代码（可选）...")
        self._coding_solution.setMinimumHeight(80)
        layout.addWidget(self._coding_solution)

        return page

    # ================================================================
    #  Populate from existing question
    # ================================================================

    def _populate_from_question(self, q: Question, q_tags: list = None):
        # Find type index
        for i, (_, type_id) in enumerate(self.QUESTION_TYPES):
            if type_id == q.question_type:
                self._type_combo.setCurrentIndex(i)
                break

        self._title_edit.setText(q.title)
        self._desc_edit.setPlainText(q.description)
        self._difficulty_combo.setCurrentText(q.difficulty)
        self._explanation_edit.setPlainText(q.explanation or "")

        if q.category_id:
            idx = self._category_combo.findData(q.category_id)
            if idx >= 0:
                self._category_combo.setCurrentIndex(idx)

        if q.source_url:
            self._url_edit.setText(q.source_url)

        # Type-specific
        if q.question_type == "multiple_choice":
            for i, choice in enumerate(q.choices):
                if i < len(self._mc_options):
                    self._mc_options[i][1].setText(choice.get("text", ""))
            idx = self._mc_correct.findText(q.correct_answer)
            if idx >= 0:
                self._mc_correct.setCurrentIndex(idx)

        elif q.question_type == "multiple_select":
            for i, choice in enumerate(q.choices):
                if i < len(self._ms_options):
                    self._ms_options[i][1].setText(choice.get("text", ""))
            correct_labels = set(q.correct_answer.split(","))
            for label, cb in self._ms_correct_checks:
                cb.setChecked(label in correct_labels)

        elif q.question_type == "fill_in_blank":
            self._fill_correct.setText(q.correct_answer)

        elif q.question_type == "short_answer":
            self._short_correct.setPlainText(q.correct_answer)

        elif q.question_type == "true_false":
            idx = self._tf_correct.findData(q.correct_answer)
            if idx >= 0:
                self._tf_correct.setCurrentIndex(idx)

        elif q.question_type == "coding":
            idx = self._coding_language.findText(q.language)
            if idx >= 0:
                self._coding_language.setCurrentIndex(idx)
            self._coding_solution.setPlainText(q.solution or "")

        # Tags
        if q_tags:
            existing_ids = {t.id for t in q_tags}
            for i in range(self._tag_list.count()):
                item = self._tag_list.item(i)
                if item.data(Qt.UserRole) in existing_ids:
                    item.setCheckState(Qt.Checked)

    # ================================================================
    #  Events
    # ================================================================

    def _on_type_changed(self, index: int):
        self._type_stack.setCurrentIndex(index)

    def _on_accept(self):
        title = self._title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "验证失败", "请输入题目名称。")
            return
        self.accept()

    # ================================================================
    #  Collect data
    # ================================================================

    def get_question_data(self) -> dict:
        """Return the question data entered by the user."""
        qtype = self._type_combo.currentData()

        # Tag IDs
        tag_ids = []
        for i in range(self._tag_list.count()):
            item = self._tag_list.item(i)
            if item.checkState() == Qt.Checked:
                tag_ids.append(item.data(Qt.UserRole))

        data = {
            "title": self._title_edit.text().strip(),
            "question_type": qtype,
            "description": self._desc_edit.toPlainText(),
            "difficulty": self._difficulty_combo.currentText(),
            "category_id": self._category_combo.currentData() or None,
            "tag_ids": tag_ids,
            "explanation": self._explanation_edit.toPlainText(),
            "source_url": self._url_edit.text().strip() or None,
            "choices": [],
            "correct_answer": "",
            "language": "python",
            "solution": "",
        }

        if qtype == "multiple_choice":
            choices = []
            for lbl_edit, text_edit in self._mc_options:
                text = text_edit.text().strip()
                if text:
                    choices.append({"label": lbl_edit.text(), "text": text})
            data["choices"] = choices
            data["correct_answer"] = self._mc_correct.currentText()

        elif qtype == "multiple_select":
            choices = []
            correct = []
            for lbl_edit, text_edit in self._ms_options:
                text = text_edit.text().strip()
                if text:
                    choices.append({"label": lbl_edit.text(), "text": text})
            for label, cb in self._ms_correct_checks:
                if cb.isChecked():
                    correct.append(label)
            data["choices"] = choices
            data["correct_answer"] = ",".join(correct)

        elif qtype == "fill_in_blank":
            data["correct_answer"] = self._fill_correct.text().strip()

        elif qtype == "short_answer":
            data["correct_answer"] = self._short_correct.toPlainText().strip()

        elif qtype == "true_false":
            data["choices"] = [
                {"label": "True", "text": "正确"},
                {"label": "False", "text": "错误"},
            ]
            data["correct_answer"] = self._tf_correct.currentData()

        elif qtype == "coding":
            data["language"] = self._coding_language.currentText()
            data["solution"] = self._coding_solution.toPlainText()

        return data
