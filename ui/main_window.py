"""Main application window — assembles all panels, menus, and signal wiring."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QSplitter,
    QStatusBar,
    QLabel,
    QMessageBox,
)

from models.question import Question
from models.chat import ChatMessage, ChatSession

from storage import (
    QuestionStore,
    BankStore,
    CategoryStore,
    TagStore,
    ChatStore,
    SettingsStore,
)

from llm import LLMManager, PromptTemplates

from .widgets.question_list import QuestionList
from .widgets.question_detail import QuestionDetail
from .widgets.chat_panel import ChatPanel
from .dialogs.question_dialog import QuestionDialog
from .dialogs.settings_dialog import SettingsDialog
from .dialogs.bank_dialog import BankDialog
from .dialogs.import_dialog import ImportDialog
from .dialogs.export_dialog import ExportDialog


class MainWindow(QMainWindow):
    """Main application window with question list, detail, and AI chat panels."""

    def __init__(self, data_dir: str = "./data"):
        super().__init__()
        self.setWindowTitle("题航 TiHang — 智能刷题")
        self.setMinimumSize(1100, 700)
        self.resize(1300, 800)

        # ---- Data directory ----
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)

        # ---- Stores ----
        self._settings_store = SettingsStore(str(self._data_dir / "settings.json"))
        self._question_store = QuestionStore(str(self._data_dir / "questions.json"))
        self._bank_store = BankStore(str(self._data_dir / "banks.json"))
        self._category_store = CategoryStore(str(self._data_dir / "categories.json"))
        self._tag_store = TagStore(str(self._data_dir / "tags.json"))
        self._chat_store = ChatStore(str(self._data_dir / "chats.json"))

        # ---- Settings ----
        self._settings = self._settings_store.load()

        # ---- LLM Manager ----
        self._llm_manager = LLMManager()
        self._llm_manager.configure(self._settings)
        self._llm_manager.response_ready.connect(self._on_llm_response)
        self._llm_manager.stream_chunk.connect(self._on_llm_chunk)
        self._llm_manager.response_error.connect(self._on_llm_error)
        self._llm_manager.stream_done.connect(self._on_llm_stream_done)

        # Current session state
        self._current_session: ChatSession | None = None
        self._current_bank_id: str = "bank-default"

        # Ensure default bank exists
        self._ensure_default_bank()

        # ---- Build UI ----
        self._setup_menu_bar()
        self._setup_central_area()
        self._setup_status_bar()

        # ---- Load initial data ----
        self._refresh_bank_list()
        self._refresh_question_list()

    # ================================================================
    #  Menu Bar
    # ================================================================

    def _setup_menu_bar(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("文件(&F)")
        file_menu.addAction("新建题目 (&N)", self._on_new_question)
        file_menu.addAction("编辑题目 (&E)", self._on_edit_question)
        file_menu.addAction("删除题目 (&D)", self._on_delete_question)
        file_menu.addSeparator()
        file_menu.addAction("管理题库 (&B)...", self._on_manage_banks)
        file_menu.addSeparator()
        import_menu = file_menu.addMenu("导入 (&I)")
        import_menu.addAction("从 JSON 文件导入 (&J)...", self._on_import_json)
        import_menu.addAction("从文档导入（AI 解析）(&D)...", self._on_import_document)
        file_menu.addAction("导出题库 (&X)...", self._on_export)
        file_menu.addSeparator()
        file_menu.addAction("退出 (&Q)", self.close)

        view_menu = menu_bar.addMenu("视图(&V)")
        view_menu.addAction("刷新列表 (&R)", self._refresh_question_list)

        settings_menu = menu_bar.addMenu("设置(&S)")
        settings_menu.addAction("打开设置 (&O)...", self._on_open_settings)

        help_menu = menu_bar.addMenu("帮助(&H)")
        help_menu.addAction("关于 (&A)", self._on_about)

    # ================================================================
    #  Central Area: 3-pane splitter
    # ================================================================

    def _setup_central_area(self):
        splitter = QSplitter(Qt.Horizontal)

        # Left: Question list
        self._question_list = QuestionList()
        self._question_list.question_selected.connect(self._on_question_selected)
        self._question_list.filter_changed.connect(self._on_filter_changed)
        self._question_list.new_question.connect(self._on_new_question)
        self._question_list.bank_changed.connect(self._on_bank_changed)
        self._question_list.manage_banks.connect(self._on_manage_banks)
        splitter.addWidget(self._question_list)

        # Center: Question detail
        self._question_detail = QuestionDetail()
        self._question_detail.save_requested.connect(self._on_save_question)
        self._question_detail.status_changed.connect(self._on_status_changed)
        splitter.addWidget(self._question_detail)

        # Right: Chat panel
        self._chat_panel = ChatPanel()
        self._chat_panel.send_message.connect(self._on_send_chat)
        self._chat_panel.new_session.connect(self._on_new_chat_session)
        self._chat_panel.clear_session.connect(self._on_clear_chat)
        self._chat_panel.provider_changed.connect(self._on_provider_changed)
        self._chat_panel.stop_generation.connect(self._llm_manager.cancel_current)
        splitter.addWidget(self._chat_panel)

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 4)
        splitter.setStretchFactor(2, 3)
        splitter.setSizes([250, 500, 350])

        self.setCentralWidget(splitter)

    # ================================================================
    #  Status Bar
    # ================================================================

    def _setup_status_bar(self):
        self._status_bar = self.statusBar()
        self._status_label = QLabel("就绪")
        self._provider_label = QLabel(f"LLM: {self._settings.active_provider}")
        self._status_bar.addWidget(self._status_label)
        self._status_bar.addPermanentWidget(self._provider_label)

    # ================================================================
    #  Question CRUD handlers
    # ================================================================

    def _refresh_question_list(self):
        filters = self._question_list.get_filters()
        questions = self._question_store.filter_by(
            bank_id=filters.get("bank_id") or self._current_bank_id,
            question_type=filters.get("question_type") or None,
            difficulty=filters.get("difficulty") or None,
            status=filters.get("status") or None,
            search=filters.get("search") or None,
        )
        self._question_list.load_questions(questions)
        self._question_list.update_stats(self._question_store.count_by_status())

    def _on_filter_changed(self):
        self._refresh_question_list()

    # ---- Bank management ----

    def _ensure_default_bank(self):
        banks = self._bank_store.list_all()
        if not any(b.id == "bank-default" for b in banks):
            from models.bank import Bank
            self._bank_store.add(Bank.default_bank())

    def _refresh_bank_list(self):
        banks = self._bank_store.list_all()
        self._question_list.load_banks(banks, self._current_bank_id)

    def _on_bank_changed(self, bank_id: str):
        self._current_bank_id = bank_id
        self._refresh_question_list()
        self._question_detail.clear()
        self._chat_panel.clear_messages()
        self._current_session = None
        self._status_label.setText(f"已切换到题库")

    def _on_manage_banks(self):
        banks = self._bank_store.list_all()
        dialog = BankDialog(banks, self)
        if dialog.exec() == BankDialog.DialogCode.Accepted:
            # Save new banks
            for bank in dialog.get_new_banks():
                self._bank_store.add(bank)
            # Update renamed banks
            for bank in dialog.get_updated_banks():
                self._bank_store.update(bank)
            # Handle deleted banks — reassign questions to first remaining bank
            deleted = dialog.get_deleted_ids()
            if deleted:
                remaining = self._bank_store.list_all()
                if remaining:
                    fallback_id = remaining[0].id
                    # Reassign questions from deleted banks
                    all_qs = self._question_store.list_all()
                    for q in all_qs:
                        if q.bank_id in deleted:
                            q.bank_id = fallback_id
                            self._question_store.update(q)
                for bid in deleted:
                    self._bank_store.delete(bid)
                # Update current bank if it was deleted
                if self._current_bank_id in deleted:
                    self._current_bank_id = remaining[0].id if remaining else "bank-default"
            self._refresh_bank_list()
            self._refresh_question_list()

    def _on_question_selected(self, question_id: str):
        question = self._question_store.get_by_id(question_id)
        if not question:
            return

        category_name = ""
        if question.category_id:
            cat = self._category_store.get_by_id(question.category_id)
            if cat:
                category_name = cat.name

        tags = [
            self._tag_store.get_by_id(tid)
            for tid in question.tag_ids
            if self._tag_store.get_by_id(tid)
        ]

        self._question_detail.load_question(question, category_name, tags)

        # Update chat panel mode filter based on question type
        self._chat_panel.update_modes_for_type(question.question_type)

        # Load chat sessions
        sessions = self._chat_store.list_by_question(question_id)
        if sessions:
            self._current_session = sessions[0]
            self._chat_panel.clear_messages()
            for msg in self._current_session.messages:
                self._chat_panel.add_message(msg.role, msg.content, msg.timestamp)
        else:
            self._current_session = None
            self._chat_panel.clear_messages()

    def _on_new_question(self):
        dialog = QuestionDialog(
            self,
            categories=self._category_store.list_all(),
            tags=self._tag_store.list_all(),
        )
        if dialog.exec() == QuestionDialog.DialogCode.Accepted:
            data = dialog.get_question_data()
            q = Question.new(
                title=data["title"],
                question_type=data["question_type"],
                description=data["description"],
                difficulty=data["difficulty"],
            )
            q.bank_id = self._current_bank_id
            q.category_id = data["category_id"]
            q.tag_ids = data["tag_ids"]
            q.choices = data["choices"]
            q.correct_answer = data["correct_answer"]
            q.explanation = data["explanation"]
            q.source_url = data["source_url"]
            if data["question_type"] == "coding":
                q.language = data["language"]
                q.solution = data["solution"]
            self._question_store.add(q)
            self._refresh_question_list()
            self._question_list.select_question(q.id)
            self._on_question_selected(q.id)
            self._status_label.setText(f"已创建: {q.title}")

    def _on_edit_question(self):
        qid = self._question_detail.get_current_question_id()
        if not qid:
            QMessageBox.information(self, "提示", "请先选择一道题目。")
            return
        question = self._question_store.get_by_id(qid)
        if not question:
            return

        q_tags = [
            self._tag_store.get_by_id(tid)
            for tid in question.tag_ids
            if self._tag_store.get_by_id(tid)
        ]

        dialog = QuestionDialog(
            self,
            question=question,
            categories=self._category_store.list_all(),
            tags=self._tag_store.list_all(),
            question_tags=q_tags,
        )
        if dialog.exec() == QuestionDialog.DialogCode.Accepted:
            data = dialog.get_question_data()
            question.title = data["title"]
            question.question_type = data["question_type"]
            question.description = data["description"]
            question.difficulty = data["difficulty"]
            question.category_id = data["category_id"]
            question.tag_ids = data["tag_ids"]
            question.choices = data["choices"]
            question.correct_answer = data["correct_answer"]
            question.explanation = data["explanation"]
            question.source_url = data["source_url"]
            if data["question_type"] == "coding":
                question.language = data["language"]
                question.solution = data["solution"]
            self._question_store.update(question)
            self._refresh_question_list()
            self._load_question_to_detail(question)
            self._status_label.setText(f"已更新: {question.title}")

    def _on_delete_question(self):
        qid = self._question_detail.get_current_question_id()
        if not qid:
            QMessageBox.information(self, "提示", "请先选择一道题目。")
            return
        question = self._question_store.get_by_id(qid)
        if not question:
            return

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除题目「{question.title}」吗？\n此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._chat_store.clear_question_sessions(qid)
            self._question_store.delete(qid)
            self._question_detail.clear()
            self._chat_panel.clear_messages()
            self._current_session = None
            self._refresh_question_list()
            self._status_label.setText(f"已删除: {question.title}")

    def _on_save_question(self, question: Question):
        if self._question_store.update(question):
            self._refresh_question_list()
            self._status_label.setText(f"已保存: {question.title}")

    def _on_status_changed(self, question_id: str, new_status: str):
        question = self._question_store.get_by_id(question_id)
        if question:
            question.status = new_status
            self._question_store.update(question)
            self._refresh_question_list()

    def _load_question_to_detail(self, question: Question):
        category_name = ""
        if question.category_id:
            cat = self._category_store.get_by_id(question.category_id)
            if cat:
                category_name = cat.name
        tags = [
            self._tag_store.get_by_id(tid)
            for tid in question.tag_ids
            if self._tag_store.get_by_id(tid)
        ]
        self._question_detail.load_question(question, category_name, tags)

    # ================================================================
    #  Chat handlers
    # ================================================================

    def _on_send_chat(self, text: str, mode: str):
        qid = self._question_detail.get_current_question_id()
        question = self._question_store.get_by_id(qid) if qid else None

        system_prompt = PromptTemplates.for_mode(
            mode,
            question_description=question.description if question else "",
            choices=question.choices if question else None,
            user_answer=question.user_answer if question else "",
            correct_answer=question.correct_answer if question else "",
            user_code=question.code_submission if question else "",
            language=question.language if question else "python",
        )

        if not self._current_session and qid:
            self._current_session = self._chat_store.create_session(
                qid, f"{mode} — {question.title if question else 'Chat'}"
            )

        user_msg = ChatMessage.new_user(text)
        self._chat_panel.add_message("user", text, user_msg.timestamp)

        if self._current_session:
            self._chat_store.add_message(self._current_session.id, user_msg)

        messages = [{"role": "system", "content": system_prompt}]
        if self._current_session:
            for msg in self._current_session.messages:
                messages.append({"role": msg.role, "content": msg.content})

        worker = self._llm_manager.send_message(
            messages,
            provider_name=self._settings.active_provider,
            stream=True,
        )
        if worker:
            self._chat_panel.start_streaming()
            self._status_label.setText("AI 正在回复...")
        else:
            self._chat_panel.set_streaming_error(
                "无法连接 LLM。请检查 API Key 设置。"
            )

    def _on_llm_chunk(self, chunk: str):
        self._chat_panel.append_stream_chunk(chunk)

    def _on_llm_response(self, text: str):
        if text:
            # For non-streaming fallback
            assistant_msg = ChatMessage.new_assistant(
                text,
                provider=self._settings.active_provider,
                model="",
            )
            if self._current_session:
                self._chat_store.add_message(self._current_session.id, assistant_msg)
            self._chat_panel.add_message("assistant", text)

    def _on_llm_stream_done(self):
        self._chat_panel.finish_streaming()
        self._status_label.setText("就绪")
        stream_buffer = getattr(self._chat_panel, "_stream_buffer", "")
        if stream_buffer:
            assistant_msg = ChatMessage.new_assistant(
                stream_buffer,
                provider=self._settings.active_provider,
                model="",
            )
            if self._current_session:
                self._chat_store.add_message(self._current_session.id, assistant_msg)

    def _on_llm_error(self, error_msg: str):
        self._chat_panel.finish_streaming()
        self._chat_panel.set_streaming_error(error_msg)
        self._status_label.setText(f"错误: {error_msg[:50]}")

    def _on_new_chat_session(self):
        qid = self._question_detail.get_current_question_id()
        if not qid:
            return
        question = self._question_store.get_by_id(qid)
        title = f"Chat — {question.title}" if question else "New Chat"
        self._current_session = self._chat_store.create_session(qid, title)
        self._chat_panel.clear_messages()
        self._status_label.setText("开始新对话")

    def _on_clear_chat(self):
        self._chat_panel.clear_messages()
        self._current_session = None

    def _on_provider_changed(self, provider_name: str):
        self._settings.active_provider = provider_name
        self._settings_store.save(self._settings)
        self._llm_manager.configure(self._settings)
        self._provider_label.setText(f"LLM: {provider_name}")

    # ================================================================
    #  Import / Export
    # ================================================================

    def _on_import_json(self):
        """Import questions from a JSON file."""
        dialog = ImportDialog(
            self._current_bank_id,
            self,
            llm_manager=self._llm_manager,
            question_store=self._question_store,
        )
        if dialog.exec() == ImportDialog.DialogCode.Accepted:
            count = dialog.get_imported_count()
            self._refresh_question_list()
            self._status_label.setText(f"导入完成，共 {count} 道题目")

    def _on_import_document(self):
        """Import questions from a document (Word/PDF/TXT) with AI parsing."""
        dialog = ImportDialog(
            self._current_bank_id,
            self,
            llm_manager=self._llm_manager,
            question_store=self._question_store,
        )
        # Switch to document mode
        dialog._import_mode = "document"
        # Navigate directly to file selection page
        dialog._stack.setCurrentIndex(1)  # PAGE_FILE
        dialog._json_radio.setChecked(False)
        dialog._doc_radio.setChecked(True)

        if dialog.exec() == ImportDialog.DialogCode.Accepted:
            count = dialog.get_imported_count()
            self._refresh_question_list()
            self._status_label.setText(f"AI 解析导入完成，共 {count} 道题目")

    def _on_export(self):
        """Export questions to JSON or Markdown."""
        dialog = ExportDialog(
            self._question_store,
            self._current_bank_id,
            self,
        )
        if dialog.exec() == ExportDialog.DialogCode.Accepted:
            result = dialog.get_export_result()
            if result.success:
                self._status_label.setText(
                    f"已导出 {result.question_count} 道题目到 "
                    f"{Path(result.filepath).name}"
                )
            else:
                QMessageBox.warning(self, "导出失败", result.error_message)

    # ================================================================
    #  Settings
    # ================================================================

    def _on_open_settings(self):
        dialog = SettingsDialog(self._settings, self,
                                llm_manager=self._llm_manager)
        dialog.settings_saved.connect(self._on_settings_saved)
        dialog.exec()

    def _on_settings_saved(self, new_settings):
        self._settings = new_settings
        self._settings_store.save(self._settings)
        self._llm_manager.configure(self._settings)
        self._provider_label.setText(f"LLM: {self._settings.active_provider}")
        self._chat_panel.set_provider(self._settings.active_provider)
        self._status_label.setText("设置已保存")

    # ================================================================
    #  Help
    # ================================================================

    def _on_about(self):
        QMessageBox.about(
            self,
            "关于 题航 TiHang",
            "<h2>题航 TiHang v2.0</h2>"
            "<p><b>高度集成 LLM 的智能刷题软件</b></p>"
            "<p>支持题型：选择题 · 多选题 · 填空题 · 简答题 · 判断题 · 编程题</p>"
            "<p>集成 AI 辅导：OpenAI / Anthropic</p>"
            "<p>基于 PySide6 构建</p>",
        )
