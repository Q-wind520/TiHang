"""Store for chat sessions and messages."""

from pathlib import Path
from typing import Optional
from models.chat import ChatSession, ChatMessage
from .base_store import BaseStore


class ChatStore(BaseStore):
    """CRUD store for chat sessions stored in chats.json."""

    def __init__(self, filepath: str | Path):
        super().__init__(filepath, {"sessions": []})

    def _load_all(self) -> list[ChatSession]:
        data = self._read()
        return [ChatSession.from_dict(s) for s in data.get("sessions", [])]

    def _save_all(self, sessions: list[ChatSession]) -> None:
        self._write({"sessions": [s.to_dict() for s in sessions]})

    def create_session(self, question_id: str, title: str = "") -> ChatSession:
        session = ChatSession.new(question_id, title)
        items = self._load_all()
        items.append(session)
        self._save_all(items)
        return session

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        for s in self._load_all():
            if s.id == session_id:
                return s
        return None

    def list_by_question(self, question_id: str) -> list[ChatSession]:
        sessions = [s for s in self._load_all() if s.question_id == question_id]
        sessions.sort(key=lambda s: s.created_at, reverse=True)
        return sessions

    def add_message(self, session_id: str, message: ChatMessage) -> bool:
        items = self._load_all()
        for i, s in enumerate(items):
            if s.id == session_id:
                s.add_message(message)
                items[i] = s
                self._save_all(items)
                return True
        return False

    def delete_session(self, session_id: str) -> bool:
        items = self._load_all()
        new_items = [s for s in items if s.id != session_id]
        if len(new_items) == len(items):
            return False
        self._save_all(new_items)
        return True

    def clear_question_sessions(self, question_id: str) -> int:
        items = self._load_all()
        new_items = [s for s in items if s.question_id != question_id]
        removed = len(items) - len(new_items)
        self._save_all(new_items)
        return removed
