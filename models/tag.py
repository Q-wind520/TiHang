import uuid
from dataclasses import dataclass


@dataclass
class Tag:
    id: str = ""
    name: str = ""

    @classmethod
    def new(cls, name: str) -> "Tag":
        return cls(id=str(uuid.uuid4()), name=name)

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name}

    @classmethod
    def from_dict(cls, data: dict) -> "Tag":
        return cls(id=data.get("id", ""), name=data.get("name", ""))
