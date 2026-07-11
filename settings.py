"""
settings.py
Central settings manager for VoidBrowser.

All persistent user preferences live in config/settings.json. Nothing in
this module (or anywhere else in the app) should hard-code a preference
value -- everything is read from JSON so users can edit it directly.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent
CONFIG_DIR = ROOT_DIR / "config"
SETTINGS_PATH = CONFIG_DIR / "settings.json"


class Settings:
    """Loads, exposes, and persists browser settings."""

    def __init__(self, path: Path = SETTINGS_PATH) -> None:
        self.path = path
        self._data: dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Read settings.json from disk into memory."""
        if not self.path.exists():
            self._data = {}
            return
        with open(self.path, "r", encoding="utf-8") as fh:
            self._data = json.load(fh)

    def save(self) -> None:
        """Persist the in-memory settings back to disk."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=4)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a top-level or dotted-path setting, e.g. 'privacy.do_not_track'."""
        node: Any = self._data
        for part in key.split("."):
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                return default
        return node

    def set(self, key: str, value: Any, persist: bool = True) -> None:
        """Set a dotted-path setting and optionally persist immediately."""
        parts = key.split(".")
        node = self._data
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value
        if persist:
            self.save()

    @property
    def downloads_folder(self) -> str:
        raw = self.get("downloads_folder", "~/Downloads")
        return os.path.expanduser(raw)

    @property
    def active_theme(self) -> str:
        return self.get("active_theme", "void")

    def as_dict(self) -> dict[str, Any]:
        return dict(self._data)
