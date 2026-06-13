"""Settings dialog — API keys, model params, editor preferences, and general options."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QWidget,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QPushButton,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QStackedWidget,
    QFileDialog,
    QMessageBox,
)

from models.settings_model import Settings, ProviderConfig, EditorConfig, AppConfig
from llm.llm_manager import LLMManager


class SettingsDialog(QDialog):
    """Tabbed settings dialog with full LLM provider configuration.

    Signals:
        settings_saved(Settings) — emitted when the user clicks OK/Apply.
    """

    settings_saved = Signal(Settings)

    THEMES = [
        "monokai", "github", "dracula",
        "one-dark", "solarized-light", "solarized-dark",
    ]

    def __init__(self, settings: Settings, parent=None,
                 llm_manager: LLMManager | None = None):
        super().__init__(parent)
        self._settings = settings
        self._llm_manager = llm_manager
        self.setWindowTitle("设置")
        self.setMinimumSize(620, 480)

        layout = QVBoxLayout(self)

        tabs = QTabWidget()

        # ---- Tab 1: LLM Providers ----
        provider_tab = QWidget()
        prov_layout = QHBoxLayout(provider_tab)
        prov_layout.setContentsMargins(4, 4, 4, 4)

        # Provider list on left
        self._prov_list = QListWidget()
        self._prov_list.setMaximumWidth(130)
        self._prov_list.setMinimumWidth(100)
        self._prov_list.currentRowChanged.connect(self._on_provider_selected)
        prov_layout.addWidget(self._prov_list)

        # Provider detail stack on right
        self._prov_stack = QStackedWidget()
        self._prov_pages: dict[str, QWidget] = {}
        self._prov_widgets: dict[str, dict] = {}

        for name, config in settings.providers.items():
            self._prov_list.addItem(config.name or name)
            page, widgets = self._create_provider_page(config)
            self._prov_stack.addWidget(page)
            self._prov_pages[name] = page
            self._prov_widgets[name] = widgets

        prov_layout.addWidget(self._prov_stack, stretch=1)
        tabs.addTab(provider_tab, "🔑 LLM 提供商")

        # ---- Tab 2: Editor ----
        editor_tab = QWidget()
        editor_form = QFormLayout(editor_tab)

        self._font_family = QLineEdit(settings.editor.font_family)
        editor_form.addRow("字体:", self._font_family)

        self._font_size = QSpinBox()
        self._font_size.setRange(8, 36)
        self._font_size.setValue(settings.editor.font_size)
        editor_form.addRow("字号:", self._font_size)

        self._tab_width = QSpinBox()
        self._tab_width.setRange(2, 8)
        self._tab_width.setValue(settings.editor.tab_width)
        editor_form.addRow("Tab 宽度:", self._tab_width)

        self._line_numbers = QCheckBox()
        self._line_numbers.setChecked(settings.editor.show_line_numbers)
        editor_form.addRow("显示行号:", self._line_numbers)

        self._word_wrap = QCheckBox()
        self._word_wrap.setChecked(settings.editor.word_wrap)
        editor_form.addRow("自动换行:", self._word_wrap)

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(self.THEMES)
        theme_idx = self._theme_combo.findText(settings.editor.theme)
        if theme_idx >= 0:
            self._theme_combo.setCurrentIndex(theme_idx)
        editor_form.addRow("编辑器主题:", self._theme_combo)

        tabs.addTab(editor_tab, "✏️ 编辑器")

        # ---- Tab 3: General ----
        general_tab = QWidget()
        general_form = QFormLayout(general_tab)

        data_row = QHBoxLayout()
        self._data_dir_edit = QLineEdit(settings.app.data_dir)
        data_row.addWidget(self._data_dir_edit)
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._browse_data_dir)
        data_row.addWidget(browse_btn)
        general_form.addRow("数据目录:", data_row)

        self._language_combo = QComboBox()
        self._language_combo.addItem("中文", "zh")
        self._language_combo.addItem("English", "en")
        lang_idx = self._language_combo.findData(settings.app.language)
        if lang_idx >= 0:
            self._language_combo.setCurrentIndex(lang_idx)
        general_form.addRow("界面语言:", self._language_combo)

        tabs.addTab(general_tab, "⚙️ 通用")

        layout.addWidget(tabs)

        # ---- Bottom bar: active provider + test + buttons ----
        bottom = QHBoxLayout()
        bottom.setContentsMargins(4, 4, 4, 0)
        bottom.setSpacing(12)

        bottom.addWidget(QLabel("当前 LLM:"))

        self._active_provider_combo = QComboBox()
        for name, config in settings.providers.items():
            self._active_provider_combo.addItem(
                f"{config.name or name}", name
            )
        active_idx = self._active_provider_combo.findData(settings.active_provider)
        if active_idx >= 0:
            self._active_provider_combo.setCurrentIndex(active_idx)
        bottom.addWidget(self._active_provider_combo)

        bottom.addSpacing(16)

        self._test_btn = QPushButton("🔗 测试连接")
        self._test_btn.setToolTip("验证当前选中提供商的 API Key 是否有效")
        self._test_btn.clicked.connect(self._on_test_connection)
        bottom.addWidget(self._test_btn)

        bottom.addStretch()

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.Apply).clicked.connect(self._on_apply)
        bottom.addWidget(buttons)

        layout.addLayout(bottom)

        if self._prov_list.count() > 0:
            self._prov_list.setCurrentRow(0)

    # ------------------------------------------------------------------
    #  Provider detail page factory
    # ------------------------------------------------------------------

    def _create_provider_page(self, config: ProviderConfig) -> tuple[QWidget, dict]:
        page = QWidget()
        form = QFormLayout(page)
        form.setContentsMargins(8, 8, 8, 8)
        form.setSpacing(8)

        name_edit = QLineEdit(config.name)
        name_edit.setPlaceholderText("显示名称，如 DeepSeek")
        form.addRow("名称:", name_edit)

        api_key_edit = QLineEdit(config.api_key)
        api_key_edit.setEchoMode(QLineEdit.Password)
        api_key_edit.setPlaceholderText("输入 API 密钥...")
        form.addRow("API 密钥:", api_key_edit)

        base_url_edit = QLineEdit(config.base_url)
        base_url_edit.setPlaceholderText("https://api.example.com/v1")
        form.addRow("接口地址:", base_url_edit)

        model_edit = QLineEdit(config.model)
        model_edit.setPlaceholderText("模型标识符，如 deepseek-v4-flash")
        form.addRow("模型:", model_edit)

        # Temperature
        temp_spin = QDoubleSpinBox()
        temp_spin.setRange(0.0, 2.0)
        temp_spin.setSingleStep(0.1)
        temp_spin.setDecimals(1)
        temp_spin.setValue(config.temperature)
        temp_spin.setToolTip("0.0 = 精确确定，1.0 = 高度创造性")
        form.addRow("随机度:", temp_spin)

        # Max tokens
        max_tok_spin = QSpinBox()
        max_tok_spin.setRange(256, 131072)
        max_tok_spin.setSingleStep(256)
        max_tok_spin.setValue(config.max_tokens)
        max_tok_spin.setToolTip("生成回复的最大 Token 数量")
        form.addRow("最大 Token:", max_tok_spin)

        # Enabled
        enabled_check = QCheckBox("启用该提供商")
        enabled_check.setChecked(config.enabled)
        form.addRow("", enabled_check)

        widgets = {
            "name": name_edit,
            "api_key": api_key_edit,
            "base_url": base_url_edit,
            "model": model_edit,
            "temperature": temp_spin,
            "max_tokens": max_tok_spin,
            "enabled": enabled_check,
        }
        return page, widgets

    # ------------------------------------------------------------------
    #  Data collection
    # ------------------------------------------------------------------

    def _on_provider_selected(self, index: int):
        if 0 <= index < self._prov_stack.count():
            self._prov_stack.setCurrentIndex(index)

    def _collect_providers(self) -> dict:
        providers = {}
        for name, widgets in self._prov_widgets.items():
            providers[name] = {
                "name": widgets["name"].text(),
                "api_key": widgets["api_key"].text(),
                "base_url": widgets["base_url"].text(),
                "model": widgets["model"].text(),
                "temperature": widgets["temperature"].value(),
                "max_tokens": widgets["max_tokens"].value(),
                "enabled": widgets["enabled"].isChecked(),
            }
        return providers

    def _build_settings(self) -> Settings:
        providers_data = self._collect_providers()
        providers = {}
        for key, data in providers_data.items():
            cfg = ProviderConfig(
                name=data["name"],
                api_key=data["api_key"],
                base_url=data["base_url"],
                model=data["model"],
                enabled=data["enabled"],
                temperature=data["temperature"],
                max_tokens=data["max_tokens"],
            )
            providers[key] = cfg

        return Settings(
            active_provider=self._active_provider_combo.currentData(),
            providers=providers,
            editor=EditorConfig(
                font_family=self._font_family.text(),
                font_size=self._font_size.value(),
                tab_width=self._tab_width.value(),
                show_line_numbers=self._line_numbers.isChecked(),
                word_wrap=self._word_wrap.isChecked(),
                theme=self._theme_combo.currentText(),
            ),
            app=AppConfig(
                language=self._language_combo.currentData(),
                data_dir=self._data_dir_edit.text(),
            ),
        )

    # ------------------------------------------------------------------
    #  Dialog actions
    # ------------------------------------------------------------------

    def _on_ok(self):
        self.settings_saved.emit(self._build_settings())
        self.accept()

    def _on_apply(self):
        self.settings_saved.emit(self._build_settings())

    def _on_test_connection(self):
        """Validate the API key for the currently selected provider."""
        if not self._llm_manager:
            QMessageBox.information(
                self, "测试连接",
                "连接测试功能需要 LLM 管理器支持。\n请启动应用后再试。"
            )
            return

        # Determine which provider is selected in the list
        current_row = self._prov_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "测试连接", "请先选择一个提供商。")
            return

        provider_keys = list(self._prov_widgets.keys())
        if current_row >= len(provider_keys):
            return

        provider_key = provider_keys[current_row]
        widgets = self._prov_widgets[provider_key]

        # Temporarily configure the provider with current form values
        api_key = widgets["api_key"].text()
        base_url = widgets["base_url"].text()
        model = widgets["model"].text()

        if not api_key.strip():
            QMessageBox.warning(
                self, "测试连接",
                "请先输入 API Key。"
            )
            return

        # Build a temporary config and validate
        temp_config = {
            "api_key": api_key,
            "base_url": base_url,
            "model": model,
        }

        # Reconfigure LLM manager with current settings + temp overrides
        self._test_btn.setEnabled(False)
        self._test_btn.setText("⏳ 测试中...")

        # Force a fresh provider instance
        self._llm_manager._providers.pop(provider_key, None)
        orig_config = self._llm_manager._settings.providers.get(provider_key)

        try:
            # Temporarily swap config
            if orig_config:
                orig_dict = orig_config.to_dict()
            else:
                orig_dict = None

            from models.settings_model import ProviderConfig as PCfg
            temp_prov = PCfg.from_dict(temp_config)
            self._llm_manager._settings.providers[provider_key] = temp_prov

            valid = self._llm_manager.validate_api_key(provider_key)

            if valid:
                QMessageBox.information(
                    self, "测试连接",
                    f"✅ {widgets['name'].text() or provider_key} 连接成功！\nAPI Key 有效。"
                )
            else:
                QMessageBox.warning(
                    self, "测试连接",
                    f"❌ 连接失败。\n请检查 API Key 和 Base URL 是否正确。"
                )
        except Exception as e:
            QMessageBox.critical(
                self, "测试连接",
                f"测试过程中发生错误：\n{e}"
            )
        finally:
            # Restore original config
            if orig_dict:
                self._llm_manager._settings.providers[provider_key] = PCfg.from_dict(orig_dict)
            else:
                self._llm_manager._settings.providers.pop(provider_key, None)
            self._llm_manager._providers.pop(provider_key, None)

            self._test_btn.setEnabled(True)
            self._test_btn.setText("🔗 测试连接")

    def _browse_data_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择数据目录")
        if dir_path:
            self._data_dir_edit.setText(dir_path)
