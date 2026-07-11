"""
ui/history_popup.py
Searchable history popup with Today / Yesterday / Last Week / Most
Visited / Recently Closed buckets and per-entry or full-history deletion.
"""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit, QListWidget, QListWidgetItem, QComboBox, QPushButton, QHBoxLayout

from popup import FloatingPopup
from history import HistoryManager

BUCKETS = ["Search", "Today", "Yesterday", "Last Week", "Most Visited"]


class HistoryPopup(FloatingPopup):
    def __init__(self, parent, history_manager: HistoryManager, on_navigate: Callable[[str], None]) -> None:
        super().__init__(parent, width_ratio=0.5, height=460, anchor="center")
        self.history_manager = history_manager
        self.on_navigate = on_navigate

        top_row = QHBoxLayout()
        self.bucket_box = QComboBox()
        self.bucket_box.addItems(BUCKETS)
        self.bucket_box.currentTextChanged.connect(lambda _t: self._filter(self.input.text()))
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self._clear_all)
        top_row.addWidget(self.bucket_box)
        top_row.addWidget(clear_btn)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Search history... (Del: remove entry)")
        self.input.textChanged.connect(self._filter)
        self.input.returnPressed.connect(self._activate_current)

        self.results = QListWidget()
        self.results.itemActivated.connect(self._on_item_activated)

        self.layout_.addLayout(top_row)
        self.layout_.addWidget(self.input)
        self.layout_.addWidget(self.results)

    def open(self) -> None:
        self.input.clear()
        self._filter("")
        self.show_animated()
        self.input.setFocus()

    def _filter(self, text: str) -> None:
        self.results.clear()
        bucket = self.bucket_box.currentText()
        q = text.strip()

        if q:
            entries = self.history_manager.search(q, limit=50)
        elif bucket == "Today":
            entries = self.history_manager.bucket("today")
        elif bucket == "Yesterday":
            entries = self.history_manager.bucket("yesterday")
        elif bucket == "Last Week":
            entries = self.history_manager.bucket("last_week")
        elif bucket == "Most Visited":
            entries = self.history_manager.most_visited(30)
        else:
            entries = self.history_manager.recent(50)

        for entry in entries:
            title = entry.get("title") or entry["url"]
            item = QListWidgetItem(f"{title}  —  {entry['url']}")
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

    def _clear_all(self) -> None:
        self.history_manager.clear()
        self._filter(self.input.text())

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
                self.history_manager.delete(item.data(Qt.ItemDataRole.UserRole))
                self._filter(self.input.text())
            return
        super().keyPressEvent(event)
