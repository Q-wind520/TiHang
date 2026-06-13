"""Markdown editor widget with edit/preview tabs."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QTextEdit,
    QTextBrowser,
)


class MarkdownEditor(QWidget):
    """A simple Markdown editor with two tabs: Edit and Preview."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._tabs = QTabWidget()

        # Edit tab
        self._edit = QTextEdit()
        self._edit.setPlaceholderText("在这里记录你的笔记（支持 Markdown）...")
        self._tabs.addTab(self._edit, "✏️ 编辑")

        # Preview tab
        self._preview = QTextBrowser()
        self._preview.setOpenExternalLinks(True)
        self._tabs.addTab(self._preview, "👁 预览")

        # Update preview when switching to preview tab
        self._tabs.currentChanged.connect(self._on_tab_changed)

        layout.addWidget(self._tabs)

    def setPlainText(self, text: str) -> None:
        self._edit.setPlainText(text)
        self._update_preview()

    def toPlainText(self) -> str:
        return self._edit.toPlainText()

    def setPlaceholderText(self, text: str) -> None:
        self._edit.setPlaceholderText(text)

    def _on_tab_changed(self, index: int):
        if index == 1:  # Preview tab
            self._update_preview()

    def _update_preview(self):
        text = self._edit.toPlainText()
        html = self._md_to_html(text)
        self._preview.setHtml(html)

    @staticmethod
    def _md_to_html(text: str) -> str:
        """Simple Markdown to HTML conversion."""
        lines = text.split("\n")
        result = []
        in_code_block = False
        code_lines = []

        for line in lines:
            # Code blocks
            if line.startswith("```"):
                if in_code_block:
                    code_html = (
                        "<pre><code>"
                        + "\n".join(code_lines).replace("&", "&amp;")
                        .replace("<", "&lt;")
                        .replace(">", "&gt;")
                        + "</code></pre>"
                    )
                    result.append(code_html)
                    code_lines = []
                    in_code_block = False
                else:
                    in_code_block = True
                continue

            if in_code_block:
                code_lines.append(line)
                continue

            # Headings
            if line.startswith("### "):
                result.append(f"<h3>{line[4:]}</h3>")
            elif line.startswith("## "):
                result.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("# "):
                result.append(f"<h1>{line[2:]}</h1>")
            # Bold + italic
            elif "**" in line or "*" in line:
                line = MarkdownEditor._inline_format(line)
                if line.strip():
                    result.append(f"<p>{line}</p>")
                else:
                    result.append("<br>")
            # List items
            elif line.strip().startswith("- "):
                result.append(f"<li>{line.strip()[2:]}</li>")
            elif line.strip() and line.strip()[0].isdigit() and ". " in line:
                result.append(f"<li>{line.strip()}</li>")
            elif line.strip():
                result.append(f"<p>{line}</p>")
            else:
                result.append("<br>")

        # Close unclosed code block
        if in_code_block:
            code_html = (
                "<pre><code>"
                + "\n".join(code_lines).replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                + "</code></pre>"
            )
            result.append(code_html)

        return "\n".join(result)

    @staticmethod
    def _inline_format(text: str) -> str:
        """Convert inline bold and italic markers."""
        # Bold **text**
        import re

        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
        # Italic *text*
        text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
        return text
