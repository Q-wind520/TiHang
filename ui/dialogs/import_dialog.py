"""Import dialog — choose format, select file, preview & confirm import.

Supports two modes:
  - JSON file import
  - Document import (Word/PDF/TXT) with LLM-powered parsing
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QRadioButton,
    QButtonGroup,
    QStackedWidget,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QMessageBox,
    QProgressBar,
    QDialogButtonBox,
    QGroupBox,
    QWidget,
)

from llm.llm_manager import LLMManager
from llm.prompt_templates import PromptTemplates
from services.importer import ImportService, ImportResult


PAGE_FORMAT = 0
PAGE_FILE = 1
PAGE_PROCESSING = 2
PAGE_PREVIEW = 3
PAGE_RESULT = 4


class ImportDialog(QDialog):
    """Wizard-style dialog for importing questions."""

    def __init__(self, current_bank_id: str, parent=None,
                 llm_manager: LLMManager | None = None,
                 question_store=None):
        super().__init__(parent)
        self.setWindowTitle("导入题库")
        self.setMinimumSize(680, 520)
        self.resize(720, 560)

        self._current_bank_id = current_bank_id
        self._llm_manager = llm_manager
        self._import_service = ImportService(question_store) if question_store else None
        self._selected_file: str = ""
        self._import_mode: str = "json"  # "json" or "document"
        self._parsed_questions: list[dict] = []
        self._import_count: int = 0
        self._import_summary: str = ""
        self._llm_worker = None

        self._setup_ui()
        self._stack.setCurrentIndex(PAGE_FORMAT)

    # ------------------------------------------------------------------
    #  Public getters (called after accept)
    # ------------------------------------------------------------------

    def get_imported_count(self) -> int:
        """Return the number of successfully imported questions."""
        return self._import_count

    def get_import_summary(self) -> str:
        """Return a human-readable summary string."""
        return self._import_summary

    # ------------------------------------------------------------------
    #  UI Setup
    # ------------------------------------------------------------------

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        self._stack = QStackedWidget()
        layout.addWidget(self._stack)

        self._setup_page_format()
        self._setup_page_file()
        self._setup_page_processing()
        self._setup_page_preview()
        self._setup_page_result()

    # ==================================================================
    #  Page 0: Format Selection
    # ==================================================================

    def _setup_page_format(self):
        page = QWidget()
        vbox = QVBoxLayout(page)
        vbox.addStretch()

        title = QLabel("<h2>选择导入方式</h2>")
        title.setAlignment(Qt.AlignCenter)
        vbox.addWidget(title)
        vbox.addSpacing(20)

        self._format_group = QButtonGroup(self)
        self._json_radio = QRadioButton("从 JSON 文件导入")
        self._doc_radio = QRadioButton("从 Word / PDF / TXT 文档导入（AI 解析）")
        self._format_group.addButton(self._json_radio, 0)
        self._format_group.addButton(self._doc_radio, 1)
        self._json_radio.setChecked(True)

        for rb in [self._json_radio, self._doc_radio]:
            rb.setMinimumHeight(36)
            vbox.addWidget(rb)

        vbox.addSpacing(30)

        next_btn = QPushButton("下一步 →")
        next_btn.setMinimumHeight(32)
        next_btn.clicked.connect(self._on_format_next)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(next_btn)
        vbox.addLayout(btn_layout)
        vbox.addStretch()

        self._stack.addWidget(page)

    # ==================================================================
    #  Page 1: File Selection
    # ==================================================================

    def _setup_page_file(self):
        page = QWidget()
        vbox = QVBoxLayout(page)

        title = QLabel("<h2>选择文件</h2>")
        vbox.addWidget(title)

        self._file_label = QLabel("未选择文件")
        self._file_label.setWordWrap(True)
        self._file_label.setStyleSheet("color: #888; padding: 8px;")
        vbox.addWidget(self._file_label)

        select_btn = QPushButton("选择文件...")
        select_btn.setMinimumHeight(32)
        select_btn.clicked.connect(self._on_select_file)
        vbox.addWidget(select_btn)

        vbox.addSpacing(8)

        self._file_preview_label = QLabel("文件预览:")
        vbox.addWidget(self._file_preview_label)
        self._file_preview = QTextEdit()
        self._file_preview.setReadOnly(True)
        self._file_preview.setMaximumHeight(200)
        vbox.addWidget(self._file_preview)

        vbox.addStretch()

        # Nav buttons
        btn_layout = QHBoxLayout()
        back_btn = QPushButton("← 返回")
        back_btn.clicked.connect(lambda: self._stack.setCurrentIndex(PAGE_FORMAT))
        btn_layout.addWidget(back_btn)
        btn_layout.addStretch()
        self._start_import_btn = QPushButton("开始导入")
        self._start_import_btn.setMinimumHeight(32)
        self._start_import_btn.clicked.connect(self._on_start_import)
        self._start_import_btn.setEnabled(False)
        btn_layout.addWidget(self._start_import_btn)
        vbox.addLayout(btn_layout)

        self._stack.addWidget(page)

    # ==================================================================
    #  Page 2: LLM Processing Overlay (document mode only)
    # ==================================================================

    def _setup_page_processing(self):
        page = QWidget()
        vbox = QVBoxLayout(page)
        vbox.addStretch()

        self._processing_label = QLabel("<h3>正在使用 AI 解析文档...</h3>")
        self._processing_label.setAlignment(Qt.AlignCenter)
        vbox.addWidget(self._processing_label)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)  # indeterminate
        self._progress_bar.setMaximumHeight(24)
        vbox.addWidget(self._progress_bar)

        vbox.addSpacing(16)

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self._on_cancel_llm)
        cancel_layout = QHBoxLayout()
        cancel_layout.addStretch()
        cancel_layout.addWidget(cancel_btn)
        cancel_layout.addStretch()
        vbox.addLayout(cancel_layout)

        vbox.addStretch()
        self._stack.addWidget(page)

    # ==================================================================
    #  Page 3: Preview & Confirm
    # ==================================================================

    def _setup_page_preview(self):
        page = QWidget()
        vbox = QVBoxLayout(page)

        title = QLabel("<h2>预览确认</h2>")
        vbox.addWidget(title)

        self._preview_summary = QLabel("")
        self._preview_summary.setStyleSheet("color: #4CAF50; font-weight: bold;")
        vbox.addWidget(self._preview_summary)

        # Table
        self._preview_table = QTableWidget()
        self._preview_table.setColumnCount(4)
        self._preview_table.setHorizontalHeaderLabels(["状态", "标题", "题型", "难度"])
        self._preview_table.horizontalHeader().setStretchLastSection(True)
        self._preview_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._preview_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._preview_table.setMinimumHeight(250)
        vbox.addWidget(self._preview_table)

        # Duplicate action
        dup_layout = QHBoxLayout()
        dup_layout.addWidget(QLabel("重复题目处理:"))
        self._dup_combo = QComboBox()
        self._dup_combo.addItem("跳过重复", "skip")
        self._dup_combo.addItem("替换重复", "replace")
        self._dup_combo.addItem("保留两者", "keep_both")
        dup_layout.addWidget(self._dup_combo)
        dup_layout.addStretch()
        vbox.addLayout(dup_layout)

        # Nav buttons
        btn_layout = QHBoxLayout()
        back_btn = QPushButton("← 返回")
        back_btn.clicked.connect(self._on_preview_back)
        btn_layout.addWidget(back_btn)
        btn_layout.addStretch()
        self._confirm_btn = QPushButton("确认导入")
        self._confirm_btn.setMinimumHeight(32)
        self._confirm_btn.clicked.connect(self._on_confirm_import)
        btn_layout.addWidget(self._confirm_btn)
        vbox.addLayout(btn_layout)

        self._stack.addWidget(page)

    # ==================================================================
    #  Page 4: Result
    # ==================================================================

    def _setup_page_result(self):
        page = QWidget()
        vbox = QVBoxLayout(page)
        vbox.addStretch()

        self._result_title = QLabel("<h2>导入完成！</h2>")
        self._result_title.setAlignment(Qt.AlignCenter)
        vbox.addWidget(self._result_title)

        vbox.addSpacing(16)

        self._result_detail = QLabel("")
        self._result_detail.setAlignment(Qt.AlignCenter)
        self._result_detail.setStyleSheet("font-size: 14px;")
        vbox.addWidget(self._result_detail)

        vbox.addSpacing(16)

        self._result_errors_label = QLabel("")
        self._result_errors_label.setWordWrap(True)
        self._result_errors_label.setStyleSheet("color: #f44336;")
        vbox.addWidget(self._result_errors_label)

        vbox.addSpacing(24)

        done_btn = QPushButton("完成")
        done_btn.setMinimumHeight(32)
        done_btn.clicked.connect(self.accept)
        done_layout = QHBoxLayout()
        done_layout.addStretch()
        done_layout.addWidget(done_btn)
        done_layout.addStretch()
        vbox.addLayout(done_layout)

        vbox.addStretch()
        self._stack.addWidget(page)

    # ==================================================================
    #  Slots — Format Selection
    # ==================================================================

    def _on_format_next(self):
        self._import_mode = "json" if self._json_radio.isChecked() else "document"
        self._selected_file = ""
        self._file_label.setText("未选择文件")
        self._file_preview.clear()
        self._start_import_btn.setEnabled(False)
        self._stack.setCurrentIndex(PAGE_FILE)

    # ==================================================================
    #  Slots — File Selection
    # ==================================================================

    def _on_select_file(self):
        if self._import_mode == "json":
            filepath, _ = QFileDialog.getOpenFileName(
                self, "选择 JSON 文件", "", "JSON 文件 (*.json)"
            )
        else:
            filepath, _ = QFileDialog.getOpenFileName(
                self,
                "选择文档",
                "",
                "文档文件 (*.docx *.pdf *.txt);;Word 文档 (*.docx);;PDF 文件 (*.pdf);;文本文件 (*.txt)",
            )

        if filepath:
            self._selected_file = filepath
            self._file_label.setText(filepath)
            self._start_import_btn.setEnabled(True)

            # Preview for JSON and TXT files
            if filepath.lower().endswith(".json"):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        preview = f.read()[:2000]
                    self._file_preview.setPlainText(preview)
                except Exception as e:
                    self._file_preview.setPlainText(f"无法预览: {e}")
            elif filepath.lower().endswith(".txt"):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        preview = f.read()[:2000]
                except UnicodeDecodeError:
                    with open(filepath, "r", encoding="gbk") as f:
                        preview = f.read()[:2000]
                self._file_preview.setPlainText(preview)
            else:
                self._file_preview.setPlainText("（不支持预览此文件格式）")

    def _on_start_import(self):
        if not self._selected_file:
            return

        if self._import_mode == "json":
            self._do_json_import()
        else:
            self._do_document_import()

    # ==================================================================
    #  JSON Import
    # ==================================================================

    def _do_json_import(self):
        if not self._import_service:
            self._show_error("导入服务未初始化。")
            return

        result = self._import_service.parse_json_file(self._selected_file)

        if not result.questions:
            self._show_error(
                "文件中没有可导入的题目。\n" +
                "\n".join(result.errors) if result.errors else ""
            )
            return

        self._parsed_questions = result.questions
        self._populate_preview_table()

    # ==================================================================
    #  Document Import (LLM)
    # ==================================================================

    def _do_document_import(self):
        if not self._llm_manager:
            self._show_error("LLM 管理器未初始化。请在设置中配置 API Key。")
            return

        # Extract text
        try:
            text = ImportService.extract_text_from_file(self._selected_file)
        except Exception as e:
            self._show_error(f"文档解析失败: {e}")
            return

        if not text.strip():
            self._show_error("文档中未提取到任何文本内容。")
            return

        # Show truncation warning
        from services.importer import MAX_DOC_TEXT_LENGTH
        if len(text) >= MAX_DOC_TEXT_LENGTH:
            text = text[:MAX_DOC_TEXT_LENGTH]
            self._processing_label.setText(
                "<h3>正在使用 AI 解析文档...</h3>"
                "<p style='color:#ff9800;font-size:12px;'>文档较长，已截取前 "
                "8000 字符发送给 AI。长文档可能无法完整解析所有题目。</p>"
            )
        else:
            self._processing_label.setText("<h3>正在使用 AI 解析文档...</h3>")

        # Show processing page
        self._stack.setCurrentIndex(PAGE_PROCESSING)

        # Build message and send to LLM
        system_prompt = PromptTemplates.for_document_parse(text)
        messages = [{"role": "user", "content": system_prompt}]

        worker = self._llm_manager.send_message(
            messages,
            provider_name="",  # use active provider
            stream=False,
        )

        if not worker:
            self._stack.setCurrentIndex(PAGE_FILE)
            self._show_error(
                "LLM 不可用。请检查：\n"
                "1. 在 设置 > LLM 提供商 中配置了 API Key\n"
                "2. 当前 Provider 已启用"
            )
            return

        self._llm_worker = worker
        worker.finished.connect(self._on_llm_response)
        worker.error.connect(self._on_llm_error)

    def _on_llm_response(self, response_text: str):
        self._llm_worker = None
        questions, errors = ImportService.parse_llm_response(response_text)

        if not questions and errors:
            # Show raw response and errors
            self._stack.setCurrentIndex(PAGE_FILE)
            detail = "\n".join(errors)
            self._show_error(
                f"AI 返回的内容无法解析。\n\n错误详情:\n{detail}\n\n"
                f"AI 原始返回:\n{response_text[:500]}..."
            )
            return

        self._parsed_questions = questions
        # Run duplicate detection
        if self._import_service and self._import_service._question_store:
            all_existing = self._import_service._question_store.list_all()
            self._import_service._check_duplicates(
                self._parsed_questions, all_existing
            )

        self._populate_preview_table()

    def _on_llm_error(self, error_msg: str):
        self._llm_worker = None
        self._stack.setCurrentIndex(PAGE_FILE)
        self._show_error(f"AI 解析失败: {error_msg}")

    def _on_cancel_llm(self):
        if self._llm_manager:
            self._llm_manager.cancel_current()
        self._llm_worker = None
        self._stack.setCurrentIndex(PAGE_FILE)

    # ==================================================================
    #  Preview Table
    # ==================================================================

    def _populate_preview_table(self):
        table = self._preview_table
        table.setRowCount(0)

        valid_count = 0
        dup_count = 0
        error_count = 0

        for q_dict in self._parsed_questions:
            row = table.rowCount()
            table.insertRow(row)

            status = q_dict.get("_import_status", "valid")
            is_dup = q_dict.get("_is_duplicate", False)

            if status == "error":
                error_count += 1
                status_text = "❌ 错误"
            elif is_dup:
                dup_count += 1
                status_text = "🔁 重复"
                valid_count += 1
            else:
                valid_count += 1
                status_text = "✅ 新"

            # Status
            status_item = QTableWidgetItem(status_text)
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row, 0, status_item)

            # Title
            title = q_dict.get("title", "（无标题）")
            title_item = QTableWidgetItem(title)
            title_item.setFlags(title_item.flags() & ~Qt.ItemIsEditable)
            if status == "error":
                title_item.setToolTip(
                    "\n".join(q_dict.get("_import_errors", []))
                )
                title_item.setForeground(Qt.red)
            table.setItem(row, 1, title_item)

            # Type
            type_name = q_dict.get("question_type", "?")
            from config.constants import QuestionType
            try:
                type_name = QuestionType.from_str(type_name).display_name()
            except Exception:
                pass
            type_item = QTableWidgetItem(type_name)
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row, 2, type_item)

            # Difficulty
            diff = q_dict.get("difficulty", "?")
            diff_display = {"easy": "简单", "medium": "中等", "hard": "困难"}.get(diff, diff)
            diff_item = QTableWidgetItem(diff_display)
            diff_item.setFlags(diff_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row, 3, diff_item)

        summary_parts = [f"共 {len(self._parsed_questions)} 道题目"]
        if valid_count:
            summary_parts.append(f"{valid_count} 道可导入")
        if dup_count:
            summary_parts.append(f"{dup_count} 道重复")
        if error_count:
            summary_parts.append(f"{error_count} 道有错误")
        self._preview_summary.setText(" · ".join(summary_parts))

        self._stack.setCurrentIndex(PAGE_PREVIEW)

    def _on_preview_back(self):
        if self._import_mode == "json":
            self._stack.setCurrentIndex(PAGE_FILE)
        else:
            self._stack.setCurrentIndex(PAGE_FORMAT)

    # ==================================================================
    #  Confirm Import
    # ==================================================================

    def _on_confirm_import(self):
        if not self._import_service:
            self._show_error("导入服务未初始化。")
            return

        # Collect valid, non-errored questions
        selected = [
            q for q in self._parsed_questions
            if q.get("_import_status") != "error"
        ]

        if not selected:
            QMessageBox.information(self, "提示", "没有可导入的题目。")
            return

        dup_action = self._dup_combo.currentData() or "skip"
        result = self._import_service.bulk_add(
            selected, self._current_bank_id, duplicate_action=dup_action
        )

        self._import_count = result.success_count
        self._import_summary = (
            f"成功导入 {result.success_count} 道，"
            f"跳过 {result.skipped_count} 道"
        )

        self._result_detail.setText(
            f"✅ 成功导入: {result.success_count} 道<br>"
            f"⏭️ 跳过: {result.skipped_count} 道"
        )

        if result.errors:
            self._result_errors_label.setText(
                "错误详情:\n" + "\n".join(result.errors[:5])
            )

        self._stack.setCurrentIndex(PAGE_RESULT)

    # ==================================================================
    #  Helpers
    # ==================================================================

    def _show_error(self, message: str):
        QMessageBox.warning(self, "导入错误", message)
