"""Store for problem categories."""

from pathlib import Path
from typing import Optional
from models.category import Category
from .base_store import BaseStore


class CategoryStore(BaseStore):
    """CRUD store for categories stored in categories.json."""

    def __init__(self, filepath: str | Path):
        super().__init__(filepath, {"categories": []})

    def _load_all(self) -> list[Category]:
        data = self._read()
        return [Category.from_dict(c) for c in data.get("categories", [])]

    def _save_all(self, categories: list[Category]) -> None:
        self._write({"categories": [c.to_dict() for c in categories]})

    def list_all(self) -> list[Category]:
        items = self._load_all()
        items.sort(key=lambda c: c.sort_order)
        return items

    def get_by_id(self, category_id: str) -> Optional[Category]:
        for c in self._load_all():
            if c.id == category_id:
                return c
        return None

    def add(self, category: Category) -> Category:
        items = self._load_all()
        items.append(category)
        self._save_all(items)
        return category

    def update(self, category: Category) -> bool:
        items = self._load_all()
        for i, c in enumerate(items):
            if c.id == category.id:
                items[i] = category
                self._save_all(items)
                return True
        return False

    def delete(self, category_id: str) -> bool:
        items = self._load_all()
        new_items = [c for c in items if c.id != category_id]
        if len(new_items) == len(items):
            return False
        self._save_all(new_items)
        return True
