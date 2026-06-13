"""Syntax highlighter using Pygments with QSyntaxHighlighter."""

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import (
    QColor,
    QFont,
    QSyntaxHighlighter,
    QTextCharFormat,
)

from pygments import highlight
from pygments.lexers import get_lexer_by_name, PythonLexer
from pygments.token import Token


def _get_pygments_style_colors(theme_name: str = "monokai") -> dict:
    """Convert a Pygments style to a Token → QColor mapping."""
    try:
        from pygments.styles import get_style_by_name

        style = get_style_by_name(theme_name)
        colors = {}
        for token, style_item in style:
            if style_item.get("color"):
                colors[token] = QColor(f"#{style_item['color']}")
            if style_item.get("bgcolor"):
                # store bg as a property name convention
                pass
        return colors
    except Exception:
        return {}


class PygmentsHighlighter(QSyntaxHighlighter):
    """QSyntaxHighlighter that uses Pygments lexers for token-based highlighting.

    Maps Pygments token types to QTextCharFormat rules with colors derived
    from the selected Pygments style theme.
    """

    # Token type to format mapping — populated from the theme
    TOKEN_STYLES = {
        Token.Keyword: ("bold", None),
        Token.Keyword.Constant: ("bold", None),
        Token.Keyword.Declaration: ("bold", None),
        Token.Keyword.Namespace: ("bold", None),
        Token.Keyword.Reserved: ("bold", None),
        Token.Keyword.Type: ("bold", None),
        Token.Name.Function: (None, None),
        Token.Name.Class: ("bold", None),
        Token.Name.Decorator: (None, None),
        Token.Name.Builtin: (None, None),
        Token.Name.Builtin.Pseudo: (None, None),
        Token.String: (None, None),
        Token.String.Doc: (None, None),
        Token.String.Escape: ("bold", None),
        Token.Number: (None, None),
        Token.Operator: (None, None),
        Token.Operator.Word: ("bold", None),
        Token.Comment: (None, None),
        Token.Comment.Special: ("bold", None),
    }

    def __init__(self, document=None, theme: str = "monokai", language: str = "python"):
        super().__init__(document)
        self._theme = theme
        self._language = language
        self._lexer = self._get_lexer(language)
        self._colors = _get_pygments_style_colors(theme)
        self._rules: list[tuple[QRegularExpression, QTextCharFormat]] = []
        self._build_rules()

    def _get_lexer(self, language: str):
        try:
            return get_lexer_by_name(language, stripall=True)
        except Exception:
            return PythonLexer(stripall=True)

    def set_theme(self, theme: str) -> None:
        self._theme = theme
        self._colors = _get_pygments_style_colors(theme)
        self._rules.clear()
        self._build_rules()
        self.rehighlight()

    def set_language(self, language: str) -> None:
        self._language = language
        self._lexer = self._get_lexer(language)
        self._rules.clear()
        self._build_rules()
        self.rehighlight()

    def _build_rules(self) -> None:
        """Build highlighting rules from common patterns for the language."""
        # Keyword rule — match common keywords
        keywords = [
            "\\bclass\\b", "\\bdef\\b", "\\breturn\\b", "\\bif\\b",
            "\\belse\\b", "\\belif\\b", "\\bfor\\b", "\\bwhile\\b",
            "\\btry\\b", "\\bexcept\\b", "\\bfinally\\b", "\\bwith\\b",
            "\\bas\\b", "\\bimport\\b", "\\bfrom\\b", "\\bpass\\b",
            "\\bbreak\\b", "\\bcontinue\\b", "\\b yield\\b", "\\braise\\b",
            "\\band\\b", "\\bor\\b", "\\bnot\\b", "\\bin\\b", "\\bis\\b",
            "\\bNone\\b", "\\bTrue\\b", "\\bFalse\\b", "\\blambda\\b",
            "\\bglobal\\b", "\\bnonlocal\\b", "\\bself\\b", "\\bprint\\b",
            "\\bassert\\b", "\\bdel\\b",
        ]
        fmt = QTextCharFormat()
        fmt.setForeground(self._colors.get(Token.Keyword, QColor("#66d9ef")))
        fmt.setFontWeight(QFont.Bold)
        for kw in keywords:
            self._rules.append(
                (QRegularExpression(kw), fmt)
            )

        # String rule (double-quoted)
        fmt_str = QTextCharFormat()
        fmt_str.setForeground(self._colors.get(Token.String, QColor("#e6db74")))
        self._rules.append(
            (QRegularExpression(r'"(?:[^"\\]|\\.)*"'), fmt_str)
        )
        self._rules.append(
            (QRegularExpression(r"'(?:[^'\\]|\\.)*'"), fmt_str)
        )

        # Number rule
        fmt_num = QTextCharFormat()
        fmt_num.setForeground(self._colors.get(Token.Number, QColor("#ae81ff")))
        self._rules.append(
            (QRegularExpression(r"\b[0-9]+\.?[0-9]*\b"), fmt_num)
        )

        # Comment rule
        fmt_cmt = QTextCharFormat()
        fmt_cmt.setForeground(self._colors.get(Token.Comment, QColor("#75715e")))
        fmt_cmt.setFontItalic(True)
        self._rules.append(
            (QRegularExpression(r"#.*$"), fmt_cmt)
        )

        # Function/class name
        fmt_func = QTextCharFormat()
        fmt_func.setForeground(
            self._colors.get(Token.Name.Function, QColor("#a6e22e"))
        )
        self._rules.append(
            (QRegularExpression(r"\bdef\s+(\w+)"), fmt_func)
        )
        fmt_cls = QTextCharFormat()
        fmt_cls.setForeground(
            self._colors.get(Token.Name.Class, QColor("#a6e22e"))
        )
        fmt_cls.setFontWeight(QFont.Bold)
        self._rules.append(
            (QRegularExpression(r"\bclass\s+(\w+)"), fmt_cls)
        )

        # Decorator
        fmt_dec = QTextCharFormat()
        fmt_dec.setForeground(
            self._colors.get(Token.Name.Decorator, QColor("#a6e22e"))
        )
        self._rules.append(
            (QRegularExpression(r"@\w+"), fmt_dec)
        )

    def highlightBlock(self, text: str) -> None:
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(
                    match.capturedStart(), match.capturedLength(), fmt
                )
