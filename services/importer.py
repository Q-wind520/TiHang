"""Import logic: JSON parsing, document text extraction, LLM response parsing, bulk-add."""

import json
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

from models.question import Question


@dataclass
class ImportResult:
    """Result of an import operation."""

    success_count: int = 0
    skipped_count: int = 0
    errors: list[str] = field(default_factory=list)
    questions: list[dict] = field(default_factory=list)


VALID_QUESTION_TYPES = {
    "multiple_choice", "multiple_select", "fill_in_blank",
    "short_answer", "true_false", "coding",
}
VALID_DIFFICULTIES = {"easy", "medium", "hard"}
CHOICE_BASED_TYPES = {"multiple_choice", "multiple_select", "true_false"}
MAX_DOC_TEXT_LENGTH = 8000


class ImportService:
    """Handles importing questions from JSON files and documents (via LLM)."""

    def __init__(self, question_store):
        self._question_store = question_store

    # ------------------------------------------------------------------
    #  JSON Import
    # ------------------------------------------------------------------

    def parse_json_file(self, filepath: str) -> ImportResult:
        """Read a JSON file, validate each entry, return ImportResult."""
        result = ImportResult()

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
        except (OSError, UnicodeDecodeError) as e:
            result.errors.append(f"无法读取文件: {e}")
            return result

        if not content:
            result.errors.append("文件为空。")
            return result

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            result.errors.append(f"JSON 格式错误: {e}")
            return result

        # Support two formats: {"questions": [...]} or [...]
        if isinstance(data, list):
            questions = data
        elif isinstance(data, dict):
            if "questions" in data and isinstance(data["questions"], list):
                questions = data["questions"]
            else:
                # Treat as single question dict
                questions = [data]
        else:
            result.errors.append("JSON 顶层必须是数组或包含 'questions' 数组的对象。")
            return result

        for i, q_dict in enumerate(questions):
            if not isinstance(q_dict, dict):
                result.errors.append(f"第 {i + 1} 条不是有效的 JSON 对象。")
                continue

            errors = self.validate_question_dict(q_dict, i)
            if errors:
                q_dict["_import_status"] = "error"
                q_dict["_import_errors"] = errors
            else:
                q_dict["_import_status"] = "valid"

            result.questions.append(q_dict)

        # Run duplicate detection
        all_existing = self._question_store.list_all()
        self._check_duplicates(result.questions, all_existing)

        return result

    def validate_question_dict(self, data: dict, index: int = 0) -> list[str]:
        """Validate a single question dict. Returns list of error messages (empty = valid)."""
        errors = []

        # Required string fields
        title = data.get("title", "")
        if not isinstance(title, str) or not title.strip():
            errors.append(f"题目 {index + 1}: 'title' 不能为空")

        qtype = data.get("question_type", "")
        if qtype not in VALID_QUESTION_TYPES:
            errors.append(
                f"题目 {index + 1}: 'question_type' 无效 '{qtype}'，"
                f"合法值: {', '.join(sorted(VALID_QUESTION_TYPES))}"
            )

        description = data.get("description", "")
        if not isinstance(description, str) or not description.strip():
            errors.append(f"题目 {index + 1}: 'description' 不能为空")

        difficulty = data.get("difficulty", "medium")
        if difficulty not in VALID_DIFFICULTIES:
            errors.append(
                f"题目 {index + 1}: 'difficulty' 无效 '{difficulty}'，"
                f"合法值: {', '.join(sorted(VALID_DIFFICULTIES))}"
            )

        # Choices validation for choice-based types
        if qtype in CHOICE_BASED_TYPES:
            choices = data.get("choices", [])
            if not isinstance(choices, list) or len(choices) == 0:
                errors.append(f"题目 {index + 1}: 选择题必须有 'choices' 列表")
            else:
                labels = {c.get("label", "") for c in choices if isinstance(c, dict)}
                correct = data.get("correct_answer", "")
                if qtype == "multiple_choice" and correct not in labels:
                    errors.append(
                        f"题目 {index + 1}: correct_answer '{correct}' 不在选项标签中"
                    )
                elif qtype == "multiple_select":
                    # Comma-separated labels — each must be a valid label
                    parts = [p.strip() for p in correct.split(",") if p.strip()]
                    for p in parts:
                        if p not in labels:
                            errors.append(
                                f"题目 {index + 1}: correct_answer 中的 '{p}' 不在选项标签中"
                            )

        return errors

    # ------------------------------------------------------------------
    #  Document Text Extraction
    # ------------------------------------------------------------------

    @staticmethod
    def extract_text_from_file(filepath: str) -> str:
        """Extract text from .docx, .pdf, or .txt file. Truncates to MAX_DOC_TEXT_LENGTH."""
        suffix = Path(filepath).suffix.lower()

        if suffix == ".txt":
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    text = f.read()
            except UnicodeDecodeError:
                with open(filepath, "r", encoding="gbk") as f:
                    text = f.read()
            return text[:MAX_DOC_TEXT_LENGTH]

        elif suffix == ".docx":
            return ImportService._extract_docx_text(filepath)[:MAX_DOC_TEXT_LENGTH]

        elif suffix == ".pdf":
            return ImportService._extract_pdf_text(filepath)[:MAX_DOC_TEXT_LENGTH]

        else:
            raise ValueError(f"不支持的文件格式: {suffix}。支持的格式: .txt, .docx, .pdf")

    @staticmethod
    def _extract_docx_text(filepath: str) -> str:
        """Extract text from a .docx file using zipfile + xml.etree."""
        paragraphs = []
        with zipfile.ZipFile(filepath, "r") as z:
            if "word/document.xml" not in z.namelist():
                raise ValueError("无效的 .docx 文件: 找不到 word/document.xml")
            xml_content = z.read("word/document.xml")
            root = ET.fromstring(xml_content)
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            for p in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
                texts = []
                for t in p.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"):
                    if t.text:
                        texts.append(t.text)
                if texts:
                    paragraphs.append("".join(texts))
        return "\n\n".join(paragraphs)

    @staticmethod
    def _extract_pdf_text(filepath: str) -> str:
        """Extract text from a PDF file using PyPDF2."""
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            raise ImportError(
                "需要 PyPDF2 库来解析 PDF 文件。请运行: pip install PyPDF2"
            )
        reader = PdfReader(filepath)
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n\n".join(pages)

    # ------------------------------------------------------------------
    #  LLM Response Parsing
    # ------------------------------------------------------------------

    @staticmethod
    def parse_llm_response(text: str) -> tuple:
        """Parse LLM response into (questions_list, error_messages).

        Handles markdown code fences and raw JSON.
        Returns (list[dict], list[str]).
        """
        errors = []
        questions = []
        json_text = text.strip()

        # Strip markdown code fences
        if json_text.startswith("```"):
            # Find first newline — fence may be ```json or just ```
            first_newline = json_text.find("\n")
            if first_newline != -1:
                json_text = json_text[first_newline + 1:]
            # Remove trailing fence
            if json_text.endswith("```"):
                json_text = json_text[:-3]
            json_text = json_text.strip()

        try:
            parsed = json.loads(json_text)
        except json.JSONDecodeError as e:
            errors.append(f"AI 返回的内容无法解析为 JSON: {e}")
            return questions, errors

        if not isinstance(parsed, list):
            errors.append("AI 返回的 JSON 不是数组格式。")
            return questions, errors

        # Validate each question
        importer = ImportService.__new__(ImportService)
        for i, q_dict in enumerate(parsed):
            if not isinstance(q_dict, dict):
                errors.append(f"第 {i + 1} 条不是有效的 JSON 对象。")
                continue

            validation_errors = importer.validate_question_dict(q_dict, i)
            if validation_errors:
                errors.extend(validation_errors)
                q_dict["_import_status"] = "error"
                q_dict["_import_errors"] = validation_errors
            else:
                q_dict["_import_status"] = "valid"

            questions.append(q_dict)

        return questions, errors

    # ------------------------------------------------------------------
    #  Duplicate Detection
    # ------------------------------------------------------------------

    def _check_duplicates(self, imported: list[dict], existing: list[Question]) -> None:
        """Annotate imported questions with _is_duplicate and _duplicate_of fields."""
        existing_titles = {q.title.strip().lower(): q.id for q in existing}
        for q_dict in imported:
            if q_dict.get("_import_status") == "error":
                continue
            title = (q_dict.get("title") or "").strip().lower()
            if title in existing_titles:
                q_dict["_is_duplicate"] = True
                q_dict["_duplicate_of"] = existing_titles[title]
            else:
                q_dict["_is_duplicate"] = False
                q_dict["_duplicate_of"] = None

    # ------------------------------------------------------------------
    #  Bulk Add
    # ------------------------------------------------------------------

    def bulk_add(
        self,
        questions: list[dict],
        bank_id: str,
        duplicate_action: str = "skip",
    ) -> ImportResult:
        """Add validated questions to the store. Returns ImportResult with counts."""
        result = ImportResult()
        existing_all = {q.title.strip().lower(): q for q in self._question_store.list_all()}

        for q_dict in questions:
            if q_dict.get("_import_status") == "error":
                result.skipped_count += 1
                continue

            title = (q_dict.get("title") or "").strip().lower()
            is_dup = title in existing_all

            if is_dup:
                if duplicate_action == "skip":
                    result.skipped_count += 1
                    continue
                elif duplicate_action == "replace":
                    old_q = existing_all[title]
                    self._question_store.delete(old_q.id)
                # "keep_both": proceed normally (new ID)

            try:
                # Build a clean dict for Question.from_dict — strip internal fields
                clean = {
                    k: v for k, v in q_dict.items()
                    if not k.startswith("_")
                }
                clean["bank_id"] = bank_id

                question = Question.from_dict(clean)
                # Always generate fresh ID + timestamps
                question.id = Question.new().id
                question.created_at = Question.new().created_at
                question.updated_at = question.created_at

                self._question_store.add(question)
                result.success_count += 1

                if is_dup and duplicate_action == "keep_both":
                    existing_all[title] = question

            except Exception as e:
                result.errors.append(f"导入失败 '{q_dict.get('title', '?')}': {e}")
                result.skipped_count += 1

        return result
