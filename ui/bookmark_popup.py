"""
ui/bookmark_popup.py
Searchable bookmarks popup with Favorites / Pinned / Recently Added /
Imported categories.
"""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit, QListWidget, QListWidgetItem, QComboBox

from popup import FloatingPopup, shorten
from bookmarks import BookmarkManager

CATEGORIES = ["All", "Favorites", "Pinned", "Recently Added", "Imported"]


class BookmarkPopup(FloatingPopup):
    def __init__(self, parent, bookmark_manager: BookmarkManager, on_navigate: Callable[[str], None]) -> None:
        super().__init__(parent, width_ratio=0.45, height=440, anchor="center")
        self.bookmark_manager = bookmark_manager
        self.on_navigate = on_navigate

        self.category_box = QComboBox()
        self.category_box.addItems(CATEGORIES)
        self.category_box.currentTextChanged.connect(lambda _t: self._filter(self.input.text()))

        self.input = QLineEdit()
        self.input.setPlaceholderText("Search bookmarks... (Del: remove)")
        self.input.textChanged.connect(self._filter)
        self.input.returnPressed.connect(self._activate_current)

        self.results = QListWidget()
        self.results.itemActivated.connect(self._on_item_activated)

        self.layout_.addWidget(self.category_box)
        self.layout_.addWidget(self.input)
        self.layout_.addWidget(self.results)

    def open(self) -> None:
        self.input.clear()
        self._filter("")
        self.show_animated()
        self.input.setFocus()

    def _filter(self, text: str) -> None:
        self.results.clear()
        category = self.category_box.currentText()
        if category == "Favorites":
            entries = self.bookmark_manager.favorites()
        elif category == "All":
            entries = self.bookmark_manager.all()
        else:
            entries = self.bookmark_manager.by_category(category)
    
        q = text.lower().strip()
        for entry in entries:
            if q and q not in entry["title"].lower() and q not in entry["url"].lower():
                continue
            star = "★ " if entry.get("favorite") else ""
            item = QListWidgetItem(f"{star}{shorten(entry['title'], 30)}  —  {shorten(entry['url'])}")
            item.setData(Qt.ItemDataRole.UserRole, entry["url"])
            self.results.addItem(item)
        if self.results.count():
            self.results.setCurrentRow(0)
    
            q = text.lower().strip()
            for entry in entries:
                if q and q not in entry["title"].lower() and q not in entry["url"].lower():
                    continue
                star = "★ " if entry.get("favorite") else ""
                item = QListWidgetItem(f"{star}{entry['title']}  —  {entry['url']}")
                item.setData(Qt.ItemDataRole.UserRole, entry["url"])
                self.results.addItem(item)
            if self.results.count():
                self.results.setCurrentRow(0)

    def _activate_current(self) -> None:
        self._on_item_activated(self.results.currentItem())

    def _on_item_activated(self, item: QListWidgetItem | None) -> None:
        if item is None:
            return
        url = item.data(Qt.ItemDataRole.UserRole)
        self.close()
        self.on_navigate(url)

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Down:
            self.results.setCurrentRow(min(self.results.currentRow() + 1, self.results.count() - 1))
            return
        if event.key() == Qt.Key.Key_Up:
            self.results.setCurrentRow(max(self.results.currentRow() - 1, 0))
            return
        if event.key() == Qt.Key.Key_Delete:
            item = self.results.currentItem()
            if item:
                self.bookmark_manager.remove(item.data(Qt.ItemDataRole.UserRole))
                self._filter(self.input.text())
            return
        super().keyPressEvent(event)
