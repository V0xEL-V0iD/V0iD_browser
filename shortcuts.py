"""
shortcuts.py
Loads config/shortcuts.json and binds every action to a QShortcut on the
main window. No keybinding is ever hard-coded in Python -- users rebind
everything by editing JSON (or eventually through the settings popup).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtWidgets import QWidget

ROOT_DIR = Path(__file__).resolve().parent
SHORTCUTS_PATH = ROOT_DIR / "config" / "shortcuts.json"


class ShortcutManager:
    """Reads shortcuts.json and wires QShortcut objects to callbacks."""

    def __init__(self, parent: QWidget, path: Path = SHORTCUTS_PATH) -> None:
        self.parent = parent
        self.path = path
        self._bindings: dict[str, str] = {}
        self._vim_bindings: dict[str, str] = {}
        self._active_shortcuts: dict[str, QShortcut] = {}
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self._bindings = {}
            self._vim_bindings = {}
            return
        with open(self.path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        self._vim_bindings = data.pop("vim", {})
        self._bindings = data

    def key_for(self, action: str) -> str | None:
        return self._bindings.get(action)

    def vim_key_for(self, action: str) -> str | None:
        return self._vim_bindings.get(action)

    def bind(self, action: str, callback: Callable[[], None]) -> None:
        """Bind a named action (from shortcuts.json) to a Python callback."""
        key_sequence = self._bindings.get(action)
        if not key_sequence:
            return
        shortcut = QShortcut(QKeySequence(key_sequence), self.parent)
        shortcut.activated.connect(callback)
        self._active_shortcuts[action] = shortcut

    def rebind(self, action: str, new_sequence: str) -> None:
        """Rebind an action at runtime and persist to disk."""
        self._bindings[action] = new_sequence
        if action in self._active_shortcuts:
            self._active_shortcuts[action].setKey(QKeySequence(new_sequence))
        self._save()

    def _save(self) -> None:
        out = dict(self._bindings)
        out["vim"] = self._vim_bindings
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=4)

    def all_bindings(self) -> dict[str, str]:
        return dict(self._bindings)

    def vim_bindings(self) -> dict[str, str]:
        return dict(self._vim_bindings)
