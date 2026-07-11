"""
ui/command_palette.py
A VS Code-style command palette. Functionally it's the same registry-
driven fuzzy list as the launcher, but visually anchored near the top
of the window and focused on in-browser actions (reload, split view,
clear cache, toggle vim mode, etc.) rather than "open app" style entries.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit, QListWidget, QListWidgetItem

from popup import FloatingPopup
from commands import CommandRegistry


class CommandPalette(FloatingPopup):
    def __init__(self, parent, registry: CommandRegistry) -> None:
        super().__init__(parent, width_ratio=0.45, height=380, anchor="top")
        self.registry = registry

        self.input = QLineEdit()
        self.input.setPlaceholderText("> Type a command...")
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
        query = text.lstrip(">").strip()
        for cmd in self.registry.search(query)[:30]:
            label = f"{cmd.category}: {cmd.title}"
            if cmd.shortcut:
                label += f"    [{cmd.shortcut}]"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, cmd.id)
            self.results.addItem(item)
        if self.results.count():
            self.results.setCurrentRow(0)

    def _activate_current(self) -> None:
        item = self.results.currentItem()
        if item:
            self._on_item_activated(item)

    def _on_item_activated(self, item: QListWidgetItem) -> None:
        command_id = item.data(Qt.ItemDataRole.UserRole)
        self.close()
        self.registry.run(command_id)

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Down:
            self.results.setCurrentRow(min(self.results.currentRow() + 1, self.results.count() - 1))
            return
        if event.key() == Qt.Key.Key_Up:
            self.results.setCurrentRow(max(self.results.currentRow() - 1, 0))
            return
        super().keyPressEvent(event)
