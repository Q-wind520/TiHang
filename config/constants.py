from enum import Enum


class Difficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

    @classmethod
    def from_str(cls, value: str) -> "Difficulty":
        for d in cls:
            if d.value == value:
                return d
        return cls.EASY


class QuestionType(Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    MULTIPLE_SELECT = "multiple_select"
    FILL_IN_BLANK = "fill_in_blank"
    SHORT_ANSWER = "short_answer"
    TRUE_FALSE = "true_false"
    CODING = "coding"

    @classmethod
    def from_str(cls, value: str) -> "QuestionType":
        for qt in cls:
            if qt.value == value:
                return qt
        return cls.MULTIPLE_CHOICE

    def display_name(self) -> str:
        names = {
            "multiple_choice": "单选题",
            "multiple_select": "多选题",
            "fill_in_blank": "填空题",
            "short_answer": "简答题",
            "true_false": "判断题",
            "coding": "编程题",
        }
        return names.get(self.value, self.value)


class QuestionStatus(Enum):
    UNANSWERED = "unanswered"
    CORRECT = "correct"
    INCORRECT = "incorrect"
    # Coding-specific
    UNSOLVED = "unsolved"
    ATTEMPTED = "attempted"
    SOLVED = "solved"

    @classmethod
    def from_str(cls, value: str) -> "QuestionStatus":
        for s in cls:
            if s.value == value:
                return s
        return cls.UNANSWERED

    def display_name(self) -> str:
        names = {
            "unanswered": "未答",
            "correct": "正确",
            "incorrect": "错误",
            "unsolved": "未解决",
            "attempted": "尝试中",
            "solved": "已解决",
        }
        return names.get(self.value, self.value)


class ProviderType(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
