"""
history.py
Tracks visited pages in data/history.json and provides search /
time-bucketed queries (Today, Yesterday, Last Week, Most Visited).
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent
HISTORY_PATH = ROOT_DIR / "data" / "history.json"


class HistoryManager:
    def __init__(self, path: Path = HISTORY_PATH) -> None:
        self.path = path
        self._entries: list[dict[str, Any]] = []
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self._entries = []
            return
        with open(self.path, "r", encoding="utf-8") as fh:
            self._entries = json.load(fh)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(self._entries, fh, indent=2)

    def visit(self, url: str, title: str = "") -> None:
        """Record a page visit, bumping visit_count if the URL repeats."""
        if url.startswith("void://"):
            return
        now = datetime.now().isoformat(timespec="seconds")
        for entry in self._entries:
            if entry["url"] == url:
                entry["visit_count"] = entry.get("visit_count", 1) + 1
                entry["last_visited"] = now
                entry["title"] = title or entry.get("title", "")
                self.save()
                return
        self._entries.append(
            {
                "url": url,
                "title": title,
                "first_visited": now,
                "last_visited": now,
                "visit_count": 1,
            }
        )
        self.save()

    def delete(self, url: str) -> None:
        self._entries = [e for e in self._entries if e["url"] != url]
        self.save()

    def clear(self) -> None:
        self._entries = []
        self.save()

    def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        q = query.lower()
        matches = [
            e for e in self._entries
            if q in e["url"].lower() or q in e.get("title", "").lower()
        ]
        matches.sort(key=lambda e: e["last_visited"], reverse=True)
        return matches[:limit]

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        return sorted(self._entries, key=lambda e: e["last_visited"], reverse=True)[:limit]

    def most_visited(self, limit: int = 10) -> list[dict[str, Any]]:
        return sorted(self._entries, key=lambda e: e.get("visit_count", 0), reverse=True)[:limit]

    def bucket(self, name: str) -> list[dict[str, Any]]:
        """Return entries for 'today', 'yesterday', or 'last_week'."""
        now = datetime.now()
        results = []
        for e in self._entries:
            try:
                visited = datetime.fromisoformat(e["last_visited"])
            except ValueError:
                continue
            if name == "today" and visited.date() == now.date():
                results.append(e)
            elif name == "yesterday" and visited.date() == (now - timedelta(days=1)).date():
                results.append(e)
            elif name == "last_week" and (now - visited) <= timedelta(days=7):
                results.append(e)
        results.sort(key=lambda e: e["last_visited"], reverse=True)
        return results
