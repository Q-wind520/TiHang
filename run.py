#!/usr/bin/env python3
"""Entry point for 题航/TiHang — 高度集成 LLM 的智能刷题软件."""

import sys
import os
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt


def main():
    # Ensure the project root is on sys.path
    project_root = Path(__file__).resolve().parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # Data directory — can be overridden via env var
    data_dir = os.environ.get("TIHANG_DATA_DIR", str(project_root / "data"))

    app = QApplication(sys.argv)
    app.setApplicationName("题航")
    app.setOrganizationName("TiHang")

    # Load global stylesheet
    qss_path = project_root / "assets" / "styles" / "app.qss"
    if qss_path.exists():
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    # Qt6 handles high-DPI automatically — no explicit attributes needed.

    from ui.main_window import MainWindow

    window = MainWindow(data_dir=data_dir)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
