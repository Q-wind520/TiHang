"""Export dialog — select format, filter questions, choose output path and export."""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QComboBox,
    QLineEdit,
    QPushButton,
    QLabel,
    QRadioButton,
    QButtonGroup,
    QCheckBox,
    QFileDialog,
    QMessageBox,
    QGroupBox,
    QDialogButtonBox,
)

from services.exporter import ExportService, ExportResult


class ExportDialog(QDialog):
    """Modal dialog for exporting questions to JSON or Markdown."""

    def __init__(self, question_store, current_bank_id: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("导出题库")
        self.setMinimumSize(480, 360)

        self._question_store = question_store
        self._current_bank_id = current_bank_id
        self._export_service = ExportService(question_store)
        self._result: ExportResult | None = None

        self._setup_ui()
        self._refresh_count()

    def get_export_result(self) -> ExportResult:
        """Return the result of the export operation after dialog is accepted."""
        return self._result or ExportResult()

    # ------------------------------------------------------------------
    #  UI Setup
    # ------------------------------------------------------------------

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # ---- Format selection ----
        fmt_group = QGroupBox("导出格式")
        fmt_layout = QVBoxLayout(fmt_group)

        self._fmt_group = QButtonGroup(self)
        self._json_radio = QRadioButton("JSON (.json)")
        self._md_radio = QRadioButton("Markdown (.md)")
        self._fmt_group.addButton(self._json_radio, 0)
        self._fmt_group.addButton(self._md_radio, 1)
        self._json_radio.setChecked(True)
        fmt_layout.addWidget(self._json_radio)
        fmt_layout.addWidget(self._md_radio)

        # Include answers checkbox (only relevant for JSON)
        self._include_answer_cb = QCheckBox("包含答案和解析")
        self._include_answer_cb.setChecked(True)
        fmt_layout.addWidget(self._include_answer_cb)

        self._json_radio.toggled.connect(self._on_format_toggled)

        layout.addWidget(fmt_group)

        # ---- Filter options ----
        filter_group = QGroupBox("筛选条件（可选）")
        filter_form = QFormLayout(filter_group)

        self._type_combo = QComboBox()
        self._type_combo.addItem("全部题型", "")
        from config.constants import QuestionType
        for qt in QuestionType:
            self._type_combo.addItem(qt.display_name(), qt.value)
        filter_form.addRow("题型:", self._type_combo)

        self._difficulty_combo = QComboBox()
        self._difficulty_combo.addItem("全部难度", "")
        self._difficulty_combo.addItem("简单", "easy")
        self._difficulty_combo.addItem("中等", "medium")
        self._difficulty_combo.addItem("困难", "hard")
        filter_form.addRow("难度:", self._difficulty_combo)

        self._type_combo.currentIndexChanged.connect(self._on_filter_changed)
        self._difficulty_combo.currentIndexChanged.connect(self._on_filter_changed)

        layout.addWidget(filter_group)

        # ---- Match count ----
        self._count_label = QLabel("共匹配 0 道题目")
        layout.addWidget(self._count_label)

        # ---- Output path ----
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("输出路径:"))
        self._path_edit = QLineEdit()
        self._path_edit.setPlaceholderText("选择或输入输出文件路径...")
        path_layout.addWidget(self._path_edit)
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._on_browse)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)

        # ---- Buttons ----
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # ------------------------------------------------------------------
    #  Slots
    # ------------------------------------------------------------------

    def _on_format_toggled(self, checked: bool):
        """Show/hide the 'include answers' checkbox based on format."""
        # Only show for JSON
        is_json = self._json_radio.isChecked()
        self._include_answer_cb.setVisible(is_json)

    def _on_filter_changed(self):
        self._refresh_count()

    def _on_browse(self):
        is_json = self._json_radio.isChecked()
        if is_json:
            name_filter = "JSON 文件 (*.json)"
            default_suffix = ".json"
        else:
            name_filter = "Markdown 文件 (*.md)"
            default_suffix = ".md"

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "导出题库",
            f"questions{default_suffix}",
            name_filter,
        )
        if filepath:
            self._path_edit.setText(filepath)

    def _refresh_count(self):
        qtype = self._type_combo.currentData() or None
        difficulty = self._difficulty_combo.currentData() or None
        questions = self._export_service.get_filtered_questions(
            self._current_bank_id,
            question_type=qtype,
            difficulty=difficulty,
        )
        self._count_label.setText(f"共匹配 {len(questions)} 道题目")

    def _on_accept(self):
        filepath = self._path_edit.text().strip()
        if not filepath:
            QMessageBox.warning(self, "验证失败", "请选择输出文件路径。")
            return

        # Collect filtered questions
        qtype = self._type_combo.currentData() or None
        difficulty = self._difficulty_combo.currentData() or None
        questions = self._export_service.get_filtered_questions(
            self._current_bank_id,
            question_type=qtype,
            difficulty=difficulty,
        )

        if not questions:
            reply = QMessageBox.question(
                self,
                "确认导出",
                "当前筛选条件没有匹配的题目。是否导出空文件？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

        # Confirm overwrite
        from pathlib import Path
        if Path(filepath).exists():
            reply = QMessageBox.question(
                self,
                "文件已存在",
                f"文件 {Path(filepath).name} 已存在，是否覆盖？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

        # Export
        is_json = self._json_radio.isChecked()
        if is_json:
            include = self._include_answer_cb.isChecked()
            self._result = self._export_service.export_json(filepath, questions, include)
        else:
            self._result = self._export_service.export_markdown(filepath, questions)

        if self._result.success:
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "导出失败",
                f"导出过程中发生错误：\n{self._result.error_message}",
            )
