"""Store for question banks."""

from pathlib import Path
from typing import Optional
from models.bank import Bank
from .base_store import BaseStore


class BankStore(BaseStore):
    """CRUD store for banks stored in banks.json."""

    def __init__(self, filepath: str | Path):
        super().__init__(filepath, {"banks": []})

    def _load_all(self) -> list[Bank]:
        data = self._read()
        return [Bank.from_dict(b) for b in data.get("banks", [])]

    def _save_all(self, banks: list[Bank]) -> None:
        self._write({"banks": [b.to_dict() for b in banks]})

    def list_all(self) -> list[Bank]:
        return self._load_all()

    def get_by_id(self, bank_id: str) -> Optional[Bank]:
        for b in self._load_all():
            if b.id == bank_id:
                return b
        return None

    def add(self, bank: Bank) -> Bank:
        items = self._load_all()
        items.append(bank)
        self._save_all(items)
        return bank

    def update(self, bank: Bank) -> bool:
        items = self._load_all()
        for i, b in enumerate(items):
            if b.id == bank.id:
                items[i] = bank
                self._save_all(items)
                return True
        return False

    def delete(self, bank_id: str) -> bool:
        items = self._load_all()
        new_items = [b for b in items if b.id != bank_id]
        if len(new_items) == len(items):
            return False
        self._save_all(new_items)
        return True
