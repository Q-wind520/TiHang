import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Category:
    id: str = ""
    name: str = ""
    color: str = "#4CAF50"
    description: str = ""
    sort_order: int = 0

    @classmethod
    def new(cls, name: str, color: str = "#4CAF50", description: str = "") -> "Category":
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            color=color,
            description=description,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "description": self.description,
            "sort_order": self.sort_order,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Category":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            color=data.get("color", "#4CAF50"),
            description=data.get("description", ""),
            sort_order=data.get("sort_order", 0),
        )
