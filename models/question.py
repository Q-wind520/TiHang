"""Question data model — supports multiple-choice, fill-in-blank, short-answer,
true-false, and coding question types."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Question:
    id: str = ""
    title: str = ""
    question_type: str = "multiple_choice"  # multiple_choice|fill_in_blank|short_answer|true_false|coding
    description: str = ""
    difficulty: str = "easy"
    bank_id: str = "bank-default"
    category_id: Optional[str] = None
    tag_ids: list[str] = field(default_factory=list)

    # Type-specific fields
    choices: list[dict] = field(default_factory=list)   # [{"label":"A","text":"..."}]
    correct_answer: str = ""                             # label for MC/TF, text for fill/short
    explanation: str = ""

    # Coding-type fields (only used when question_type == "coding")
    language: str = "python"
    solution: str = ""

    # User state
    notes: str = ""
    user_answer: str = ""
    code_submission: str = ""   # only for coding type
    status: str = "unanswered"  # unanswered|correct|incorrect (attempted/solved for coding)

    source_url: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    last_practiced_at: Optional[str] = None

    @classmethod
    def new(cls, title: str = "", question_type: str = "multiple_choice",
            description: str = "", difficulty: str = "easy") -> "Question":
        now = datetime.now(timezone.utc).isoformat()
        return cls(
            id=str(uuid.uuid4()),
            title=title,
            question_type=question_type,
            description=description,
            difficulty=difficulty,
            created_at=now,
            updated_at=now,
        )

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def practice_now(self) -> None:
        self.last_practiced_at = datetime.now(timezone.utc).isoformat()

    def check_answer(self, user_answer: str) -> bool:
        """Compare user answer to correct answer. Returns True if correct."""
        self.user_answer = user_answer

        if self.question_type in ("multiple_choice", "true_false"):
            is_correct = user_answer.strip().upper() == self.correct_answer.strip().upper()
        elif self.question_type == "multiple_select":
            user_set = set(user_answer.split(","))
            correct_set = set(self.correct_answer.split(","))
            is_correct = user_set == correct_set
        elif self.question_type == "fill_in_blank":
            # Case-insensitive, trim whitespace
            is_correct = user_answer.strip().lower() == self.correct_answer.strip().lower()
        elif self.question_type == "short_answer":
            # For short answer, check if the correct answer keywords appear
            is_correct = user_answer.strip().lower() == self.correct_answer.strip().lower()
        else:
            # coding — no auto-judge
            is_correct = False

        self.status = "correct" if is_correct else "incorrect"
        self.practice_now()
        self.touch()
        return is_correct

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "question_type": self.question_type,
            "description": self.description,
            "difficulty": self.difficulty,
            "bank_id": self.bank_id,
            "category_id": self.category_id,
            "tag_ids": self.tag_ids,
            "choices": self.choices,
            "correct_answer": self.correct_answer,
            "explanation": self.explanation,
            "language": self.language,
            "solution": self.solution,
            "notes": self.notes,
            "user_answer": self.user_answer,
            "code_submission": self.code_submission,
            "status": self.status,
            "source_url": self.source_url,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_practiced_at": self.last_practiced_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Question":
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            question_type=data.get("question_type", "multiple_choice"),
            description=data.get("description", ""),
            difficulty=data.get("difficulty", "easy"),
            bank_id=data.get("bank_id", "bank-default"),
            category_id=data.get("category_id"),
            tag_ids=data.get("tag_ids", []),
            choices=data.get("choices", []),
            correct_answer=data.get("correct_answer", ""),
            explanation=data.get("explanation", ""),
            language=data.get("language", "python"),
            solution=data.get("solution", ""),
            notes=data.get("notes", ""),
            user_answer=data.get("user_answer", ""),
            code_submission=data.get("code_submission", ""),
            status=data.get("status", "unanswered"),
            source_url=data.get("source_url"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            last_practiced_at=data.get("last_practiced_at"),
        )
