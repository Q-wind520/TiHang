"""Unit tests for ExportService — JSON and Markdown export."""

import json
import os
import tempfile

import pytest

from services.exporter import ExportService, ExportResult
from models.question import Question


# ------------------------------------------------------------------
#  Fixtures
# ------------------------------------------------------------------

@pytest.fixture
def mock_store():
    class MockStore:
        def __init__(self):
            self._questions = []
        def list_all(self):
            return self._questions
        def filter_by(self, bank_id, question_type=None, difficulty=None,
                      status=None, search=None, category_id=None, tag_id=None):
            result = self._questions
            if question_type:
                result = [q for q in result if q.question_type == question_type]
            if difficulty:
                result = [q for q in result if q.difficulty == difficulty]
            return result
    return MockStore()


@pytest.fixture
def exporter(mock_store):
    return ExportService(mock_store)


@pytest.fixture
def sample_mc_question():
    q = Question.new(
        title="Python 列表 vs 元组",
        question_type="multiple_choice",
        description="Python 中列表和元组的主要区别是什么？",
        difficulty="easy",
    )
    q.choices = [
        {"label": "A", "text": "列表可变，元组不可变"},
        {"label": "B", "text": "元组可变，列表不可变"},
        {"label": "C", "text": "两者完全相同"},
        {"label": "D", "text": "两者都不可变"},
    ]
    q.correct_answer = "A"
    q.explanation = "列表（list）是可变的，元组（tuple）是不可变的。"
    return q


@pytest.fixture
def sample_coding_question():
    q = Question.new(
        title="Two Sum",
        question_type="coding",
        description="给定一个整数数组和一个目标值，找出数组中和为目标值的两个数。",
        difficulty="medium",
    )
    q.language = "python"
    q.solution = "def two_sum(nums, target):\n    seen = {}\n    for i, n in enumerate(nums):\n        diff = target - n\n        if diff in seen:\n            return [seen[diff], i]\n        seen[n] = i"
    return q


@pytest.fixture
def sample_tf_question():
    q = Question.new(
        title="Python 是面向对象的语言",
        question_type="true_false",
        description="Python 是否支持面向对象编程？",
        difficulty="easy",
    )
    q.choices = [
        {"label": "True", "text": "正确"},
        {"label": "False", "text": "错误"},
    ]
    q.correct_answer = "True"
    return q


# ------------------------------------------------------------------
#  Tests: get_filtered_questions
# ------------------------------------------------------------------

class TestGetFilteredQuestions:
    def test_no_filters_returns_all(self, exporter, mock_store, sample_mc_question, sample_coding_question):
        mock_store._questions = [sample_mc_question, sample_coding_question]
        result = exporter.get_filtered_questions("bank-default")
        assert len(result) == 2

    def test_type_filter(self, exporter, mock_store, sample_mc_question, sample_coding_question):
        mock_store._questions = [sample_mc_question, sample_coding_question]
        result = exporter.get_filtered_questions("bank-default", question_type="coding")
        assert len(result) == 1
        assert result[0].question_type == "coding"

    def test_difficulty_filter(self, exporter, mock_store, sample_mc_question, sample_coding_question):
        mock_store._questions = [sample_mc_question, sample_coding_question]
        result = exporter.get_filtered_questions("bank-default", difficulty="easy")
        assert len(result) == 1
        assert result[0].difficulty == "easy"


# ------------------------------------------------------------------
#  Tests: export_json
# ------------------------------------------------------------------

class TestExportJson:
    def test_basic_json_export(self, exporter, sample_mc_question):
        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False
        ) as f:
            tmp = f.name

        try:
            result = exporter.export_json(tmp, [sample_mc_question])
            assert result.success
            assert result.question_count == 1
            assert os.path.exists(tmp)

            with open(tmp, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert "questions" in data
            assert len(data["questions"]) == 1
            assert data["questions"][0]["title"] == "Python 列表 vs 元组"
            assert data["questions"][0]["correct_answer"] == "A"
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def test_json_without_answers(self, exporter, sample_mc_question):
        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False
        ) as f:
            tmp = f.name

        try:
            result = exporter.export_json(tmp, [sample_mc_question], include_answer=False)
            assert result.success

            with open(tmp, "r", encoding="utf-8") as f:
                data = json.load(f)
            q = data["questions"][0]
            assert q["correct_answer"] == ""
            assert q["explanation"] == ""
            assert q["status"] == "unanswered"
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def test_empty_list(self, exporter):
        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False
        ) as f:
            tmp = f.name

        try:
            result = exporter.export_json(tmp, [])
            assert result.success
            assert result.question_count == 0
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def test_creates_parent_dirs(self, exporter, sample_mc_question):
        tmpdir = tempfile.mkdtemp()
        filepath = os.path.join(tmpdir, "sub", "nested", "output.json")
        try:
            result = exporter.export_json(filepath, [sample_mc_question])
            assert result.success
            assert os.path.exists(filepath)
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)


# ------------------------------------------------------------------
#  Tests: export_markdown
# ------------------------------------------------------------------

class TestExportMarkdown:
    def test_basic_md_export(self, exporter, sample_mc_question):
        with tempfile.NamedTemporaryFile(
            suffix=".md", mode="w", delete=False, encoding="utf-8"
        ) as f:
            tmp = f.name

        try:
            result = exporter.export_markdown(tmp, [sample_mc_question])
            assert result.success
            assert result.question_count == 1
            assert os.path.exists(tmp)

            with open(tmp, "r", encoding="utf-8") as f:
                content = f.read()
            assert "## 1. Python 列表 vs 元组" in content
            assert "**题型**: 单选题" in content
            assert "### 选项" in content
            assert "- **A**. 列表可变" in content
            assert "### 正确答案" in content
            assert "### 解析" in content
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def test_md_coding_question(self, exporter, sample_coding_question):
        with tempfile.NamedTemporaryFile(
            suffix=".md", mode="w", delete=False, encoding="utf-8"
        ) as f:
            tmp = f.name

        try:
            result = exporter.export_markdown(tmp, [sample_coding_question])
            assert result.success

            with open(tmp, "r", encoding="utf-8") as f:
                content = f.read()
            assert "## 1. Two Sum" in content
            assert "**题型**: 编程题" in content
            assert "```python" in content
            assert "def two_sum" in content
            # Coding questions should NOT have choices section
            assert "### 选项" not in content
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def test_md_tf_question(self, exporter, sample_tf_question):
        with tempfile.NamedTemporaryFile(
            suffix=".md", mode="w", delete=False, encoding="utf-8"
        ) as f:
            tmp = f.name

        try:
            result = exporter.export_markdown(tmp, [sample_tf_question])
            assert result.success

            with open(tmp, "r", encoding="utf-8") as f:
                content = f.read()
            assert "**题型**: 判断题" in content
            assert "### 选项" in content
            assert "正确" in content
            assert "错误" in content
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def test_md_multiple_questions(self, exporter, sample_mc_question, sample_coding_question):
        with tempfile.NamedTemporaryFile(
            suffix=".md", mode="w", delete=False, encoding="utf-8"
        ) as f:
            tmp = f.name

        try:
            result = exporter.export_markdown(tmp, [sample_mc_question, sample_coding_question])
            assert result.success
            assert result.question_count == 2

            with open(tmp, "r", encoding="utf-8") as f:
                content = f.read()
            assert "## 1." in content
            assert "## 2." in content
            assert "---" in content
            assert "题航 TiHang" in content
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
