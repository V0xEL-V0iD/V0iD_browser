"""
ui/tab_popup.py
Searchable tab-switcher popup, opened with Ctrl+Tab. Shows every open
tab's title, URL, pinned/audio status, and lets the user switch, close,
duplicate, or pin tabs entirely from the keyboard.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit, QListWidget, QListWidgetItem

from popup import FloatingPopup
from tabs import TabManager


class TabPopup(FloatingPopup):
    def __init__(self, parent, tab_manager: TabManager) -> None:
        super().__init__(parent, width_ratio=0.45, height=420, anchor="center")
        self.tab_manager = tab_manager

        self.input = QLineEdit()
        self.input.setPlaceholderText("Search tabs... (Enter: switch, Ctrl+X: close, Ctrl+D: duplicate)")
        self.input.textChanged.connect(self._filter)
        self.input.returnPressed.connect(self._activate_current)

        self.results = QListWidget()
        self.results.itemActivated.connect(self._on_item_activated)

        self.layout_.addWidget(self.input)
        self.layout_.addWidget(self.results)

    def open(self) -> None:
        self.input.clear()
        self._filter("")
        self.show_animated()
        self.input.setFocus()

    def _filter(self, text: str) -> None:
        self.results.clear()
        q = text.lower().strip()
        for i, tab in enumerate(self.tab_manager.tabs):
            if q and q not in tab.title.lower() and q not in tab.url.lower():
                continue
            pin = "📌 " if tab.pinned else ""
            audio = "🔊 " if tab.audio else ""
            item = QListWidgetItem(f"{pin}{audio}{tab.title}  —  {tab.url}")
            item.setData(Qt.ItemDataRole.UserRole, i)
            self.results.addItem(item)
        current = self.tab_manager.active_index()
        for row in range(self.results.count()):
            if self.results.item(row).data(Qt.ItemDataRole.UserRole) == current:
                self.results.setCurrentRow(row)
                break
        else:
            if self.results.count():
                self.results.setCurrentRow(0)

    def _selected_index(self) -> int | None:
        item = self.results.currentItem()
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def _activate_current(self) -> None:
        self._on_item_activated(self.results.currentItem())

    def _on_item_activated(self, item: QListWidgetItem | None) -> None:
        if item is None:
            return
        index = item.data(Qt.ItemDataRole.UserRole)
        self.close()
        self.tab_manager.set_active(index)

    def keyPressEvent(self, event) -> None:  # noqa: N802
        mods = event.modifiers()
        if event.key() == Qt.Key.Key_Down:
            self.results.setCurrentRow(min(self.results.currentRow() + 1, self.results.count() - 1))
            return
        if event.key() == Qt.Key.Key_Up:
            self.results.setCurrentRow(max(self.results.currentRow() - 1, 0))
            return
        if mods & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_X:
            index = self._selected_index()
            if index is not None:
                self.tab_manager.close_tab(index)
                self._filter(self.input.text())
            return
        if mods & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_D:
            index = self._selected_index()
            if index is not None:
                self.tab_manager.duplicate_tab(index)
                self._filter(self.input.text())
            return
        if mods & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_P:
            index = self._selected_index()
            if index is not None:
                tab = self.tab_manager.tabs[index]
                self.tab_manager.pin_tab(index, not tab.pinned)
                self._filter(self.input.text())
            return
        super().keyPressEvent(event)
