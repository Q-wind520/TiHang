"""Unit tests for ImportService — JSON parsing, validation, LLM response parsing."""

import json
import tempfile
import os
from pathlib import Path

import pytest

from services.importer import ImportService, ImportResult, MAX_DOC_TEXT_LENGTH


# ------------------------------------------------------------------
#  Fixtures
# ------------------------------------------------------------------

@pytest.fixture
def mock_store():
    """A minimal mock question store."""
    class MockStore:
        def __init__(self):
            self._questions = []
        def list_all(self):
            return self._questions
        def add(self, q):
            self._questions.append(q)
        def delete(self, qid):
            self._questions = [q for q in self._questions if q.id != qid]
        def get_by_id(self, qid):
            for q in self._questions:
                if q.id == qid:
                    return q
            return None
    return MockStore()


@pytest.fixture
def importer(mock_store):
    return ImportService(mock_store)


@pytest.fixture
def valid_mc_question():
    return {
        "title": "What is Python?",
        "question_type": "multiple_choice",
        "description": "Pick the best answer.",
        "difficulty": "easy",
        "choices": [
            {"label": "A", "text": "A snake"},
            {"label": "B", "text": "A programming language"},
            {"label": "C", "text": "A type of food"},
            {"label": "D", "text": "None of the above"},
        ],
        "correct_answer": "B",
        "explanation": "Python is a programming language.",
    }


@pytest.fixture
def valid_coding_question():
    return {
        "title": "Two Sum",
        "question_type": "coding",
        "description": "Given an array, return indices...",
        "difficulty": "medium",
        "choices": [],
        "correct_answer": "",
        "explanation": "",
    }


# ------------------------------------------------------------------
#  Tests: validate_question_dict
# ------------------------------------------------------------------

class TestValidateQuestionDict:
    def test_valid_mc_passes(self, importer, valid_mc_question):
        errors = importer.validate_question_dict(valid_mc_question, 0)
        assert errors == []

    def test_valid_coding_passes(self, importer, valid_coding_question):
        errors = importer.validate_question_dict(valid_coding_question, 0)
        assert errors == []

    def test_valid_tf_passes(self, importer):
        q = {
            "title": "Python is OOP?",
            "question_type": "true_false",
            "description": "True or false",
            "difficulty": "easy",
            "choices": [
                {"label": "True", "text": "正确"},
                {"label": "False", "text": "错误"},
            ],
            "correct_answer": "True",
        }
        errors = importer.validate_question_dict(q, 0)
        assert errors == []

    def test_missing_title(self, importer):
        q = {"question_type": "multiple_choice", "description": "x"}
        errors = importer.validate_question_dict(q, 0)
        assert any("title" in e.lower() for e in errors)

    def test_invalid_type(self, importer):
        q = {"title": "X", "question_type": "essay", "description": "x"}
        errors = importer.validate_question_dict(q, 0)
        assert any("question_type" in e for e in errors)

    def test_invalid_difficulty(self, importer):
        q = {"title": "X", "question_type": "coding", "description": "x", "difficulty": "impossible"}
        errors = importer.validate_question_dict(q, 0)
        assert any("difficulty" in e for e in errors)

    def test_missing_description(self, importer):
        q = {"title": "X", "question_type": "short_answer"}
        errors = importer.validate_question_dict(q, 0)
        assert any("description" in e.lower() for e in errors)

    def test_mc_without_choices(self, importer):
        q = {"title": "X", "question_type": "multiple_choice", "description": "x"}
        errors = importer.validate_question_dict(q, 0)
        assert any("choices" in e.lower() for e in errors)

    def test_mc_correct_answer_not_in_labels(self, importer):
        q = {
            "title": "X",
            "question_type": "multiple_choice",
            "description": "x",
            "choices": [{"label": "A", "text": "a"}],
            "correct_answer": "Z",
        }
        errors = importer.validate_question_dict(q, 0)
        assert any("correct_answer" in e for e in errors)

    def test_fill_in_blank_no_choices_ok(self, importer):
        q = {
            "title": "Fill",
            "question_type": "fill_in_blank",
            "description": "___",
            "correct_answer": "answer",
        }
        errors = importer.validate_question_dict(q, 0)
        assert errors == []


# ------------------------------------------------------------------
#  Tests: parse_json_file
# ------------------------------------------------------------------

class TestParseJsonFile:
    def test_array_format(self, importer, valid_mc_question):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump([valid_mc_question], f)
            tmp = f.name

        try:
            result = importer.parse_json_file(tmp)
            assert len(result.errors) == 0
            assert len(result.questions) == 1
            assert result.questions[0]["_import_status"] == "valid"
        finally:
            os.unlink(tmp)

    def test_questions_wrapper_format(self, importer, valid_mc_question, valid_coding_question):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump({"questions": [valid_mc_question, valid_coding_question]}, f)
            tmp = f.name

        try:
            result = importer.parse_json_file(tmp)
            assert len(result.questions) == 2
            assert result.questions[0]["_import_status"] == "valid"
            assert result.questions[1]["_import_status"] == "valid"
        finally:
            os.unlink(tmp)

    def test_empty_file(self, importer):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write("")
            tmp = f.name

        try:
            result = importer.parse_json_file(tmp)
            assert len(result.errors) > 0
            assert len(result.questions) == 0
        finally:
            os.unlink(tmp)

    def test_invalid_json(self, importer):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write("not valid json {{{")
            tmp = f.name

        try:
            result = importer.parse_json_file(tmp)
            assert len(result.errors) > 0
        finally:
            os.unlink(tmp)

    def test_invalid_questions_marked(self, importer):
        bad_q = {"title": "", "question_type": "wrong"}
        valid_q = {
            "title": "OK",
            "question_type": "coding",
            "description": "desc",
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump([bad_q, valid_q], f)
            tmp = f.name

        try:
            result = importer.parse_json_file(tmp)
            assert len(result.questions) == 2
            assert result.questions[0]["_import_status"] == "error"
            assert result.questions[1]["_import_status"] == "valid"
        finally:
            os.unlink(tmp)


# ------------------------------------------------------------------
#  Tests: parse_llm_response
# ------------------------------------------------------------------

class TestParseLlmResponse:
    def test_plain_json_array(self):
        questions, errors = ImportService.parse_llm_response(
            json.dumps([
                {"title": "Q1", "question_type": "coding", "description": "d", "difficulty": "easy"}
            ])
        )
        assert len(questions) == 1
        assert questions[0]["title"] == "Q1"
        assert errors == []

    def test_markdown_fenced_json(self):
        response = '```json\n[{"title": "Q1", "question_type": "coding", "description": "d", "difficulty": "easy"}]\n```'
        questions, errors = ImportService.parse_llm_response(response)
        assert len(questions) == 1
        assert questions[0]["_import_status"] == "valid"

    def test_empty_array(self):
        questions, errors = ImportService.parse_llm_response("[]")
        assert len(questions) == 0
        assert errors == []

    def test_invalid_json_text(self):
        questions, errors = ImportService.parse_llm_response("hello, I found no questions")
        assert len(questions) == 0
        assert len(errors) > 0

    def test_not_an_array(self):
        questions, errors = ImportService.parse_llm_response('{"title": "not array"}')
        assert len(questions) == 0
        assert len(errors) > 0

    def test_mixed_valid_invalid(self):
        response = json.dumps([
            {"title": "", "question_type": "coding", "description": "d"},  # invalid (no title)
            {"title": "Good", "question_type": "multiple_choice", "description": "d",
             "difficulty": "hard", "choices": [{"label": "A", "text": "x"}], "correct_answer": "A"},
        ])
        questions, errors = ImportService.parse_llm_response(response)
        assert len(questions) == 2
        assert questions[0]["_import_status"] == "error"
        assert questions[1]["_import_status"] == "valid"
        assert len(errors) > 0


# ------------------------------------------------------------------
#  Tests: extract_text_from_file
# ------------------------------------------------------------------

class TestExtractText:
    def test_txt_utf8(self, importer):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("Hello, this is a test document.\nWith multiple lines.")
            tmp = f.name

        try:
            text = ImportService.extract_text_from_file(tmp)
            assert "Hello" in text
            assert "multiple lines" in text
        finally:
            os.unlink(tmp)

    def test_unsupported_format(self):
        with pytest.raises(ValueError, match="不支持的文件格式"):
            ImportService.extract_text_from_file("test.xyz")

    def test_truncation(self, importer):
        long_text = "A" * (MAX_DOC_TEXT_LENGTH + 100)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write(long_text)
            tmp = f.name

        try:
            text = ImportService.extract_text_from_file(tmp)
            assert len(text) == MAX_DOC_TEXT_LENGTH
        finally:
            os.unlink(tmp)


# ------------------------------------------------------------------
#  Tests: bulk_add
# ------------------------------------------------------------------

class TestBulkAdd:
    def test_add_new_questions(self, importer, mock_store, valid_mc_question, valid_coding_question):
        valid_mc_question["_import_status"] = "valid"
        valid_coding_question["_import_status"] = "valid"

        result = importer.bulk_add(
            [valid_mc_question, valid_coding_question],
            "bank-test",
            duplicate_action="skip",
        )
        assert result.success_count == 2
        assert result.skipped_count == 0
        assert len(mock_store.list_all()) == 2

    def test_skip_duplicates(self, importer, mock_store, valid_mc_question):
        from models.question import Question
        # Pre-add an existing question with the same title
        existing = Question.new(
            title=valid_mc_question["title"],
            question_type="multiple_choice",
            description="existing",
        )
        existing.bank_id = "bank-test"
        mock_store.add(existing)

        valid_mc_question["_import_status"] = "valid"
        result = importer.bulk_add(
            [valid_mc_question], "bank-test", duplicate_action="skip"
        )
        assert result.success_count == 0
        assert result.skipped_count == 1

    def test_replace_duplicates(self, importer, mock_store, valid_mc_question):
        from models.question import Question
        existing = Question.new(
            title=valid_mc_question["title"],
            question_type="multiple_choice",
            description="old description",
        )
        existing.bank_id = "bank-test"
        mock_store.add(existing)

        valid_mc_question["_import_status"] = "valid"
        result = importer.bulk_add(
            [valid_mc_question], "bank-test", duplicate_action="replace"
        )
        assert result.success_count == 1
        # Old one removed, new one added — count still 1
        assert len(mock_store.list_all()) == 1
        # The new description should be present
        new_q = mock_store.list_all()[0]
        assert "Pick the best answer" in new_q.description

    def test_keep_both(self, importer, mock_store, valid_mc_question):
        from models.question import Question
        existing = Question.new(
            title=valid_mc_question["title"],
            question_type="multiple_choice",
            description="existing",
        )
        existing.bank_id = "bank-test"
        mock_store.add(existing)

        valid_mc_question["_import_status"] = "valid"
        result = importer.bulk_add(
            [valid_mc_question], "bank-test", duplicate_action="keep_both"
        )
        assert result.success_count == 1
        assert len(mock_store.list_all()) == 2  # both kept

    def test_skips_errors(self, importer, mock_store):
        bad_q = {
            "title": "Bad",
            "question_type": "coding",
            "description": "d",
            "_import_status": "error",
        }
        result = importer.bulk_add([bad_q], "bank-test")
        assert result.skipped_count == 1
        assert result.success_count == 0
