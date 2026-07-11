"""
ui/url_popup.py
The floating URL/search popup, opened with Ctrl+Space (configurable).
Combines direct URL entry, search-engine queries, history, bookmarks,
and pinned sites into a single ranked, keyboard-navigable list.
"""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit, QListWidget, QListWidgetItem

from popup import FloatingPopup, shorten


class UrlPopup(FloatingPopup):
    """Zen-Browser-style centered URL bar with live suggestions."""

    def __init__(self, parent, history_manager, bookmark_manager, search_manager,
                 on_navigate: Callable[[str], None]) -> None:
        super().__init__(parent, width_ratio=0.5, height=380, anchor="top")
        self.history_manager = history_manager
        self.bookmark_manager = bookmark_manager
        self.search_manager = search_manager
        self.on_navigate = on_navigate

        self.input = QLineEdit()
        self.input.setPlaceholderText("Search or enter address...")
        self.input.textChanged.connect(self._update_suggestions)
        self.input.returnPressed.connect(self._activate_current)

        self.results = QListWidget()
        self.results.itemActivated.connect(self._on_item_activated)
        self.results.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.results.setWordWrap(False)

        self.layout_.addWidget(self.input)
        self.layout_.addWidget(self.results)

    def open(self, prefill: str = "") -> None:
        self.input.setText(prefill)
        self._update_suggestions(prefill)
        self.show_animated()
        self.input.setFocus()
        self.input.selectAll()

    def _update_suggestions(self, text: str) -> None:
        self.results.clear()
        text = text.strip()

        if not text:
            for entry in self.history_manager.recent(limit=6):
                self._add_item(entry.get("title") or entry["url"], entry["url"], "recent")
            return

        # Direct navigation / search suggestion always first
        if self.search_manager.looks_like_url(text):
            self._add_item(f"Go to {text}", text, "go")
        else:
            self._add_item(f'Search for "{text}"', text, "search")

        for entry in self.bookmark_manager.search(text)[:4]:
            self._add_item(entry["title"], entry["url"], "bookmark")

        for entry in self.history_manager.search(text, limit=6):
            self._add_item(entry.get("title") or entry["url"], entry["url"], "history")

        if self.results.count():
            self.results.setCurrentRow(0)

    def _add_item(self, label: str, value: str, kind: str) -> None:
        icon = {"go": "→", "search": "🔍", "bookmark": "★", "history": "🕑", "recent": "🕑"}.get(kind, "•")
        item = QListWidgetItem(f"{icon}  {shorten(label)}")
        item.setData(Qt.ItemDataRole.UserRole, (kind, value))
        self.results.addItem(item)

    def _activate_current(self) -> None:
        item = self.results.currentItem()
        if item is not None:
            self._on_item_activated(item)
        else:
            text = self.input.text().strip()
            if text:
                self._navigate(self.search_manager.resolve(text))

    def _on_item_activated(self, item: QListWidgetItem) -> None:
        kind, value = item.data(Qt.ItemDataRole.UserRole)
        if kind == "search":
            self._navigate(self.search_manager.query_url(value))
        else:
            self._navigate(self.search_manager.resolve(value) if kind == "go" else value)

    def _navigate(self, url: str) -> None:
        self.close()
        self.on_navigate(url)

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Down:
            self.results.setCurrentRow(min(self.results.currentRow() + 1, self.results.count() - 1))
            return
        if event.key() == Qt.Key.Key_Up:
            self.results.setCurrentRow(max(self.results.currentRow() - 1, 0))
            return
        super().keyPressEvent(event)
