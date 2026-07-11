"""
workspace.py
Manages workspaces (isolated groups of tabs) and session persistence to
data/sessions.json so browsing state survives restarts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent
SESSIONS_PATH = ROOT_DIR / "data" / "sessions.json"


class WorkspaceManager:
    """Owns the on-disk session data for every workspace."""

    def __init__(self, path: Path = SESSIONS_PATH) -> None:
        self.path = path
        self._data: dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8") as fh:
                self._data = json.load(fh)
        else:
            self._data = {"workspaces": {"main": {"tabs": [], "active_index": 0}},
                           "active_workspace": "main"}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=2)

    @property
    def active_workspace_name(self) -> str:
        return self._data.get("active_workspace", "main")

    def workspace_names(self) -> list[str]:
        return list(self._data.get("workspaces", {}).keys())

    def create_workspace(self, name: str) -> None:
        self._data.setdefault("workspaces", {})[name] = {"tabs": [], "active_index": 0}
        self.save()

    def rename_workspace(self, old: str, new: str) -> None:
        workspaces = self._data.get("workspaces", {})
        if old in workspaces and new not in workspaces:
            workspaces[new] = workspaces.pop(old)
            if self._data.get("active_workspace") == old:
                self._data["active_workspace"] = new
            self.save()

    def switch_workspace(self, name: str) -> None:
        if name in self._data.get("workspaces", {}):
            self._data["active_workspace"] = name
            self.save()

    def save_tabs(self, workspace: str, tabs: list[dict[str, Any]], active_index: int) -> None:
        """tabs is a list of {"url": str, "title": str, "pinned": bool}."""
        self._data.setdefault("workspaces", {})[workspace] = {
            "tabs": tabs,
            "active_index": active_index,
        }
        self.save()

    def load_tabs(self, workspace: str) -> tuple[list[dict[str, Any]], int]:
        ws = self._data.get("workspaces", {}).get(workspace, {"tabs": [], "active_index": 0})
        return ws.get("tabs", []), ws.get("active_index", 0)
