"""Question bank model — groups questions into named collections."""

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class Bank:
    id: str = ""
    name: str = ""
    description: str = ""
    created_at: str = ""

    @classmethod
    def new(cls, name: str, description: str = "") -> "Bank":
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    @classmethod
    def default_bank(cls) -> "Bank":
        return cls(
            id="bank-default",
            name="默认题库",
            description="系统默认题库",
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Bank":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            created_at=data.get("created_at", ""),
        )
