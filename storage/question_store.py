"""Store for exam/coding questions."""

from pathlib import Path
from typing import Optional
from models.question import Question
from .base_store import BaseStore


class QuestionStore(BaseStore):
    """CRUD store for questions stored in questions.json."""

    def __init__(self, filepath: str | Path):
        super().__init__(filepath, {"questions": []})

    def _load_all(self) -> list[Question]:
        data = self._read()
        return [Question.from_dict(q) for q in data.get("questions", [])]

    def _save_all(self, questions: list[Question]) -> None:
        self._write({"questions": [q.to_dict() for q in questions]})

    def list_all(self) -> list[Question]:
        items = self._load_all()
        items.sort(key=lambda q: q.updated_at, reverse=True)
        return items

    def get_by_id(self, question_id: str) -> Optional[Question]:
        for q in self._load_all():
            if q.id == question_id:
                return q
        return None

    def add(self, question: Question) -> Question:
        items = self._load_all()
        items.append(question)
        self._save_all(items)
        return question

    def update(self, question: Question) -> bool:
        question.touch()
        items = self._load_all()
        for i, q in enumerate(items):
            if q.id == question.id:
                items[i] = question
                self._save_all(items)
                return True
        return False

    def delete(self, question_id: str) -> bool:
        items = self._load_all()
        new_items = [q for q in items if q.id != question_id]
        if len(new_items) == len(items):
            return False
        self._save_all(new_items)
        return True

    def filter_by(
        self,
        bank_id: Optional[str] = None,
        question_type: Optional[str] = None,
        difficulty: Optional[str] = None,
        status: Optional[str] = None,
        category_id: Optional[str] = None,
        tag_id: Optional[str] = None,
        search: Optional[str] = None,
    ) -> list[Question]:
        items = self._load_all()
        if bank_id:
            items = [q for q in items if q.bank_id == bank_id]
        if question_type:
            items = [q for q in items if q.question_type == question_type]
        if difficulty:
            items = [q for q in items if q.difficulty == difficulty]
        if status:
            items = [q for q in items if q.status == status]
        if category_id:
            items = [q for q in items if q.category_id == category_id]
        if tag_id:
            items = [q for q in items if tag_id in q.tag_ids]
        if search:
            qs = search.lower()
            items = [
                q
                for q in items
                if qs in q.title.lower() or qs in q.description.lower()
            ]
        items.sort(key=lambda q: q.updated_at, reverse=True)
        return items

    def count_by_status(self) -> dict[str, int]:
        items = self._load_all()
        counts = {
            "unanswered": 0, "correct": 0, "incorrect": 0,
            "unsolved": 0, "attempted": 0, "solved": 0,
            "total": len(items),
        }
        for q in items:
            if q.status in counts:
                counts[q.status] += 1
        return counts
