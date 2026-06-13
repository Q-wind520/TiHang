"""Dialog for managing question banks — create, rename, delete."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QDialogButtonBox,
    QMessageBox,
    QInputDialog,
)

from models.bank import Bank


class BankDialog(QDialog):
    """Modal dialog for creating and deleting question banks."""

    def __init__(self, banks: list[Bank], parent=None):
        super().__init__(parent)
        self._banks = banks
        self._result_banks: list[Bank] = list(banks)
        self._deleted_ids: set[str] = set()
        self._new_banks: list[Bank] = []

        self.setWindowTitle("管理题库")
        self.setMinimumSize(450, 350)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("题库列表:"))

        self._list = QListWidget()
        self._refresh_list()
        layout.addWidget(self._list)

        # Buttons
        btn_row = QHBoxLayout()

        add_btn = QPushButton("➕ 新建题库")
        add_btn.clicked.connect(self._on_add)
        btn_row.addWidget(add_btn)

        rename_btn = QPushButton("✏️ 重命名")
        rename_btn.clicked.connect(self._on_rename)
        btn_row.addWidget(rename_btn)

        delete_btn = QPushButton("🗑 删除")
        delete_btn.clicked.connect(self._on_delete)
        btn_row.addWidget(delete_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        # OK / Cancel
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _refresh_list(self):
        self._list.clear()
        for bank in self._result_banks:
            if bank.id not in self._deleted_ids:
                item = QListWidgetItem(f"📚 {bank.name}")
                item.setData(Qt.UserRole, bank.id)
                if bank.description:
                    item.setToolTip(bank.description)
                self._list.addItem(item)

    def _on_add(self):
        name, ok = QInputDialog.getText(
            self, "新建题库", "请输入题库名称:"
        )
        if ok and name.strip():
            bank = Bank.new(name.strip())
            self._new_banks.append(bank)
            self._result_banks.append(bank)
            self._refresh_list()

    def _on_rename(self):
        item = self._list.currentItem()
        if not item:
            QMessageBox.information(self, "提示", "请先选择一个题库。")
            return
        bank_id = item.data(Qt.UserRole)
        for bank in self._result_banks:
            if bank.id == bank_id:
                name, ok = QInputDialog.getText(
                    self, "重命名题库", "请输入新名称:", text=bank.name
                )
                if ok and name.strip():
                    bank.name = name.strip()
                    self._refresh_list()
                return

    def _on_delete(self):
        item = self._list.currentItem()
        if not item:
            QMessageBox.information(self, "提示", "请先选择一个题库。")
            return
        bank_id = item.data(Qt.UserRole)

        # Don't allow deleting the last bank
        remaining = [b for b in self._result_banks
                     if b.id not in self._deleted_ids]
        if len(remaining) <= 1:
            QMessageBox.warning(self, "无法删除", "至少保留一个题库。")
            return

        reply = QMessageBox.question(
            self, "确认删除",
            "删除题库后，该题库下的所有题目将变为无题库状态。\n确定要删除吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._deleted_ids.add(bank_id)
            self._refresh_list()

    def get_new_banks(self) -> list[Bank]:
        return self._new_banks

    def get_updated_banks(self) -> list[Bank]:
        """Return banks that were renamed."""
        return [b for b in self._result_banks
                if b.id not in self._deleted_ids]

    def get_deleted_ids(self) -> set[str]:
        return self._deleted_ids
