"""Unit tests for core data models."""

import pytest
from models.question import Question
from models.bank import Bank
from models.chat import ChatMessage, ChatSession
from models.settings_model import Settings


class TestQuestion:
    def test_new_question_has_id(self):
        q = Question.new(title="Test", question_type="multiple_choice")
        assert q.id
        assert q.title == "Test"

    def test_check_answer_mc_correct(self):
        q = Question.new(title="Q1", question_type="multiple_choice")
        q.correct_answer = "A"
        result = q.check_answer("A")
        assert result is True
        assert q.status == "correct"

    def test_check_answer_mc_incorrect(self):
        q = Question.new(title="Q1", question_type="multiple_choice")
        q.correct_answer = "B"
        result = q.check_answer("A")
        assert result is False
        assert q.status == "incorrect"

    def test_to_dict_and_from_dict(self):
        q = Question.new(title="Roundtrip", question_type="coding")
        q.correct_answer = "print(42)"
        q.language = "python"
        data = q.to_dict()
        q2 = Question.from_dict(data)
        assert q2.title == q.title
        assert q2.language == "python"


class TestChatMessage:
    def test_new_user_message(self):
        msg = ChatMessage.new_user("Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_new_assistant_message(self):
        msg = ChatMessage.new_assistant("Hi!", provider="openai", model="gpt-4o")
        assert msg.role == "assistant"
        assert msg.provider == "openai"


class TestSettings:
    def test_default_active_provider(self):
        s = Settings()
        assert s.active_provider in ("openai",)
