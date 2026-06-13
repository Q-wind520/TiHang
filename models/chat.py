import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ChatMessage:
    role: str = "user"  # "user" | "assistant" | "system"
    content: str = ""
    timestamp: str = ""
    provider: Optional[str] = None
    model: Optional[str] = None

    @classmethod
    def new_user(cls, content: str) -> "ChatMessage":
        return cls(
            role="user",
            content=content,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    @classmethod
    def new_assistant(
        cls, content: str, provider: str = "", model: str = ""
    ) -> "ChatMessage":
        return cls(
            role="assistant",
            content=content,
            timestamp=datetime.now(timezone.utc).isoformat(),
            provider=provider,
            model=model,
        )

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "provider": self.provider,
            "model": self.model,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ChatMessage":
        return cls(
            role=data.get("role", "user"),
            content=data.get("content", ""),
            timestamp=data.get("timestamp", ""),
            provider=data.get("provider"),
            model=data.get("model"),
        )


@dataclass
class ChatSession:
    id: str = ""
    question_id: str = ""
    title: str = ""
    messages: list[ChatMessage] = field(default_factory=list)
    created_at: str = ""

    @classmethod
    def new(cls, question_id: str, title: str = "") -> "ChatSession":
        return cls(
            id=str(uuid.uuid4()),
            question_id=question_id,
            title=title or "New Chat",
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def add_message(self, msg: ChatMessage) -> None:
        self.messages.append(msg)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "question_id": self.question_id,
            "title": self.title,
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ChatSession":
        messages = [ChatMessage.from_dict(m) for m in data.get("messages", [])]
        return cls(
            id=data.get("id", ""),
            question_id=data.get("question_id", ""),
            title=data.get("title", ""),
            messages=messages,
            created_at=data.get("created_at", ""),
        )
