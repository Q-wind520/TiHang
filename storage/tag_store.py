"""Store for problem tags."""

from pathlib import Path
from typing import Optional
from models.tag import Tag
from .base_store import BaseStore


class TagStore(BaseStore):
    """CRUD store for tags stored in tags.json."""

    def __init__(self, filepath: str | Path):
        super().__init__(filepath, {"tags": []})

    def _load_all(self) -> list[Tag]:
        data = self._read()
        return [Tag.from_dict(t) for t in data.get("tags", [])]

    def _save_all(self, tags: list[Tag]) -> None:
        self._write({"tags": [t.to_dict() for t in tags]})

    def list_all(self) -> list[Tag]:
        return self._load_all()

    def get_by_id(self, tag_id: str) -> Optional[Tag]:
        for t in self._load_all():
            if t.id == tag_id:
                return t
        return None

    def get_by_name(self, name: str) -> Optional[Tag]:
        for t in self._load_all():
            if t.name.lower() == name.lower():
                return t
        return None

    def find_or_create(self, name: str) -> Tag:
        existing = self.get_by_name(name)
        if existing:
            return existing
        tag = Tag.new(name)
        self.add(tag)
        return tag

    def add(self, tag: Tag) -> Tag:
        items = self._load_all()
        items.append(tag)
        self._save_all(items)
        return tag

    def update(self, tag: Tag) -> bool:
        items = self._load_all()
        for i, t in enumerate(items):
            if t.id == tag.id:
                items[i] = tag
                self._save_all(items)
                return True
        return False

    def delete(self, tag_id: str) -> bool:
        items = self._load_all()
        new_items = [t for t in items if t.id != tag_id]
        if len(new_items) == len(items):
            return False
        self._save_all(new_items)
        return True
