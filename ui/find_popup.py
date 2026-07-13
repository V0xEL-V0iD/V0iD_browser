"""
ui/find_popup.py
A compact in-page find bar (Ctrl+F, or `/` in Vim mode). Incremental search
with a live match count; Enter / Shift+Enter cycle to the next / previous
result. Closing the bar clears the page's search highlight.
"""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QWidget

from popup import FloatingPopup


class FindPopup(FloatingPopup):
    """Slim find bar anchored near the top of the window."""

    def __init__(self, parent, on_search: Callable[[str, bool], None],
                 on_close: Callable[[], None]) -> None:
        super().__init__(parent, width_ratio=0.36, height=64, anchor="top")
        self._on_search = on_search
        self._on_close = on_close

        row = QWidget()
        hbox = QHBoxLayout(row)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(8)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Find in page…")
        self.input.textChanged.connect(lambda t: self._on_search(t, False))

        self.count = QLabel("")
        self.count.setObjectName("dimLabel")
        self.count.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.count.setFixedWidth(96)

        hbox.addWidget(self.input, 1)
        hbox.addWidget(self.count, 0)
        self.layout_.addWidget(row)

    def open(self, prefill: str = "") -> None:
        self.show_animated()
        self.input.setFocus()
        if prefill:
            self.input.setText(prefill)
            self.input.selectAll()
        else:
            self.input.clear()
            self.count.setText("")

    def set_count(self, active: int, total: int) -> None:
        if not self.input.text().strip():
            self.count.setText("")
        elif total <= 0:
            self.count.setText("no matches")
        else:
            self.count.setText(f"{active}/{total}")

    def keyPressEvent(self, event) -> None:  # noqa: N802 (Qt override)
        key = event.key()
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            backward = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
            self._on_search(self.input.text(), backward)
            return
        super().keyPressEvent(event)  # base handles Escape -> close

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt override)
        self._on_close()
        super().closeEvent(event)
