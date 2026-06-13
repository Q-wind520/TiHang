"""Export logic: JSON serialization and Markdown rendering for questions."""

import json
from dataclasses import dataclass, field
from pathlib import Path

from models.question import Question
from config.constants import QuestionType


@dataclass
class ExportResult:
    """Result of an export operation."""

    success: bool = False
    filepath: str = ""
    question_count: int = 0
    error_message: str = ""


class ExportService:
    """Handles exporting questions to JSON or Markdown files."""

    def __init__(self, question_store):
        self._question_store = question_store

    def get_filtered_questions(
        self,
        bank_id: str,
        question_type: str | None = None,
        difficulty: str | None = None,
    ) -> list[Question]:
        """Delegate to QuestionStore.filter_by with optional filters."""
        return self._question_store.filter_by(
            bank_id=bank_id,
            question_type=question_type or None,
            difficulty=difficulty or None,
        )

    def export_json(
        self,
        filepath: str,
        questions: list[Question],
        include_answer: bool = True,
    ) -> ExportResult:
        """Serialize questions to a JSON file."""
        try:
            data = {"questions": []}
            for q in questions:
                q_dict = q.to_dict()
                if not include_answer:
                    q_dict["correct_answer"] = ""
                    q_dict["explanation"] = ""
                    q_dict["solution"] = ""
                    q_dict["notes"] = ""
                    q_dict["user_answer"] = ""
                    q_dict["code_submission"] = ""
                    q_dict["status"] = "unanswered"
                data["questions"].append(q_dict)

            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return ExportResult(
                success=True,
                filepath=str(path),
                question_count=len(data["questions"]),
            )
        except Exception as e:
            return ExportResult(
                success=False,
                filepath=filepath,
                error_message=str(e),
            )

    def export_markdown(
        self,
        filepath: str,
        questions: list[Question],
    ) -> ExportResult:
        """Render questions as a Markdown document and write to file."""
        try:
            lines = [f"# 题航 TiHang — 题库导出", "",
                     f"共 {len(questions)} 道题目", "", "---", ""]

            for idx, q in enumerate(questions, 1):
                lines.extend(self._render_question(q, idx))

            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            return ExportResult(
                success=True,
                filepath=str(path),
                question_count=len(questions),
            )
        except Exception as e:
            return ExportResult(
                success=False,
                filepath=filepath,
                error_message=str(e),
            )

    def _render_question(self, q: Question, index: int) -> list[str]:
        """Render a single question as Markdown lines."""
        type_name = QuestionType.from_str(q.question_type).display_name()
        diff_name = {"easy": "简单", "medium": "中等", "hard": "困难"}.get(
            q.difficulty, q.difficulty
        )

        lines = [
            f"## {index}. {q.title}",
            "",
            f"**题型**: {type_name} | **难度**: {diff_name} | **ID**: `{q.id}`",
            "",
        ]

        # Description
        if q.description:
            lines.append("### 题目描述")
            lines.append("")
            lines.append(q.description)
            lines.append("")

        # Choices — only for choice-based types
        if q.question_type in ("multiple_choice", "multiple_select", "true_false") and q.choices:
            lines.append("### 选项")
            lines.append("")
            for c in q.choices:
                label = c.get("label", "?")
                text = c.get("text", "")
                lines.append(f"- **{label}**. {text}")
            lines.append("")

        # Answer
        if q.correct_answer:
            lines.append("### 正确答案")
            lines.append("")
            lines.append(q.correct_answer)
            lines.append("")

        # Explanation
        if q.explanation:
            lines.append("### 解析")
            lines.append("")
            lines.append(q.explanation)
            lines.append("")

        # Solution for coding questions
        if q.question_type == "coding" and q.solution:
            lang = q.language or "python"
            lines.append("### 参考解答")
            lines.append("")
            lines.append(f"```{lang}")
            lines.append(q.solution)
            lines.append("```")
            lines.append("")

        # Separator
        lines.append("---")
        lines.append("")
        return lines
