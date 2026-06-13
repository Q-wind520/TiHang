"""System prompt templates for different AI assistant modes.

Supports both exam-style questions (multiple-choice, fill-in-blank, short-answer,
true-false) and coding questions.
"""


class PromptTemplates:
    """Collection of system prompts formatted with question context."""

    GENERAL = (
        "你是一个专业的辅导助手。请帮助用户解答问题、理解知识点、"
        "掌握解题方法。回答应该清晰、准确、有教育意义。"
    )

    HINT = (
        "你是一个辅导导师。用户正在解答以下题目：\n"
        "---\n{question_description}\n---\n"
        "{choices_text}"
        "请给出一个**渐进式提示**，引导用户思考解题方向，"
        "但**不要直接给出完整答案**。建议他们应该考虑的角度、知识点或方法。"
    )

    EXPLAIN_ANSWER = (
        "你是一个辅导老师。用户刚刚回答了以下题目：\n"
        "---\n{question_description}\n---\n"
        "{choices_text}"
        "用户的答案：{user_answer}\n"
        "正确答案：{correct_answer}\n"
        "判题结果：{result}\n\n"
        "请详细解释：\n"
        "1. 为什么正确答案是对的\n"
        "2. 如果用户答错了，分析用户可能哪里理解有误\n"
        "3. 这道题涉及的知识点\n"
        "请保持耐心和鼓励性。"
    )

    EXPLAIN_CONCEPT = (
        "你是一个教育者。用户想理解与以下题目相关的知识点：\n"
        "---\n{question_description}\n---\n"
        "{choices_text}"
        "请清晰地解释相关的概念和解题思路，"
        "用通俗易懂的语言配合适当的例子。"
    )

    CODE_REVIEW = (
        "你是一个代码审查专家。请审查用户针对以下问题编写的解答：\n"
        "---\n{question_description}\n---\n"
        "用户的代码：\n```{language}\n{user_code}\n```\n"
        "请从以下方面给出反馈：\n"
        "1. 正确性 — 代码是否正确解决了问题？\n"
        "2. 时间/空间复杂度分析\n"
        "3. 代码风格和可读性\n"
        "4. 边界条件处理\n"
        "5. 潜在的改进建议\n"
        "请保持建设性和鼓励性。"
    )

    DOCUMENT_PARSE = (
        "你是一个专业的试题解析器。请从以下文档文本中提取所有题目，"
        "并以 JSON 数组格式返回。\n\n"
        "--- 文档文本 ---\n"
        "{document_text}\n"
        "---\n\n"
        "每道题目必须包含以下字段：\n"
        "{{\n"
        '  "title": "题目标题",\n'
        '  "question_type": "multiple_choice|multiple_select|fill_in_blank|short_answer|true_false|coding",\n'
        '  "description": "题目描述（可包含 Markdown）",\n'
        '  "difficulty": "easy|medium|hard",\n'
        '  "choices": [{{"label": "A", "text": "选项内容"}}],  // 仅选择题/判断题需要，其他类型为空数组 []\n'
        '  "correct_answer": "正确答案或参考解答",\n'
        '  "explanation": "题目解析（可选，可为空字符串）"\n'
        "}}\n\n"
        "要求：\n"
        "1. 无法确定难度时，默认为 \"medium\"\n"
        "2. 编程题（coding）的 choices 为空数组 []，correct_answer 为参考解答代码或思路描述\n"
        "3. 判断题（true_false）的 choices 严格为 "
        "[{{\"label\":\"True\",\"text\":\"正确\"}},{{\"label\":\"False\",\"text\":\"错误\"}}]\n"
        "4. 只返回 JSON 数组，不要包含任何其他文字或解释\n"
        "5. 如果文档中没有识别到任何题目，返回空数组 []\n"
        "6. 保持原文描述，不要自行编造或修改题目内容"
    )

    @classmethod
    def for_document_parse(cls, document_text: str) -> str:
        """Return the document parse prompt with the given text interpolated."""
        return cls.DOCUMENT_PARSE.format(document_text=document_text)

    @classmethod
    def for_mode(
        cls,
        mode: str,
        question_description: str = "",
        choices: list = None,
        user_answer: str = "",
        correct_answer: str = "",
        result: str = "",
        user_code: str = "",
        language: str = "python",
    ) -> str:
        """Return the system prompt for a given mode, with context filled in."""
        choices_text = cls._format_choices(choices)
        mode_lower = mode.lower()

        if mode_lower in ("hint", "ask for hint"):
            return cls.HINT.format(
                question_description=question_description or "（未提供）",
                choices_text=choices_text,
            )
        elif mode_lower in ("explain_answer", "explain answer"):
            return cls.EXPLAIN_ANSWER.format(
                question_description=question_description or "（未提供）",
                choices_text=choices_text,
                user_answer=user_answer or "（未作答）",
                correct_answer=correct_answer or "（无）",
                result=result or "（未知）",
            )
        elif mode_lower in ("explain_concept", "explain concept", "explain"):
            return cls.EXPLAIN_CONCEPT.format(
                question_description=question_description or "（未提供）",
                choices_text=choices_text,
            )
        elif mode_lower in ("code_review", "code review"):
            return cls.CODE_REVIEW.format(
                question_description=question_description or "（未提供）",
                user_code=user_code or "（未提供代码）",
                language=language or "python",
            )
        else:
            return cls.GENERAL

    @classmethod
    def _format_choices(cls, choices: list | None) -> str:
        """Format choices list into a readable string."""
        if not choices:
            return ""
        lines = ["**选项：**"]
        for c in choices:
            label = c.get("label", "")
            text = c.get("text", "")
            lines.append(f"  {label}. {text}")
        return "\n".join(lines) + "\n"

    @classmethod
    def available_modes_for_type(cls, question_type: str) -> list[tuple[str, str]]:
        """Return (display_name, mode_id) pairs valid for a question type."""
        common = [
            ("💬 通用对话", "general"),
            ("💡 请求提示", "hint"),
            ("📖 概念解释", "explain_concept"),
        ]
        exam_only = [
            ("✅ 答案解析", "explain_answer"),
        ]
        coding_only = [
            ("🔍 代码审查", "code_review"),
        ]

        if question_type == "coding":
            return common + coding_only
        else:
            return common + exam_only
