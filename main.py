#!/usr/bin/env python3
"""
main.py
Entry point for VoidBrowser -- a keyboard-first, floating-popup web
browser inspired by Omarchy, Zen Browser, and Vim.

Usage:
    python main.py
"""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from browser import Browser


def main() -> int:
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)
    app = QApplication(sys.argv)
    app.setApplicationName("VoidBrowser")
    app.setOrganizationName("VoidBrowser")

    browser = Browser(app)
    browser.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
