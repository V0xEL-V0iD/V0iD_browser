"""
bookmarks.py
Manages bookmarks stored in data/bookmarks.json, organized into
categories (Favorites, Pinned, Recently Added, Imported).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent
BOOKMARKS_PATH = ROOT_DIR / "data" / "bookmarks.json"


class BookmarkManager:
    def __init__(self, path: Path = BOOKMARKS_PATH) -> None:
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

    def add(self, url: str, title: str = "", category: str = "Recently Added",
             favorite: bool = False) -> None:
        if any(b["url"] == url for b in self._entries):
            return
        self._entries.append(
            {
                "url": url,
                "title": title or url,
                "category": category,
                "favorite": favorite,
                "added": datetime.now().isoformat(timespec="seconds"),
            }
        )
        self.save()

    def remove(self, url: str) -> None:
        self._entries = [b for b in self._entries if b["url"] != url]
        self.save()

    def toggle_favorite(self, url: str) -> None:
        for b in self._entries:
            if b["url"] == url:
                b["favorite"] = not b.get("favorite", False)
        self.save()

    def is_bookmarked(self, url: str) -> bool:
        return any(b["url"] == url for b in self._entries)

    def all(self) -> list[dict[str, Any]]:
        return list(self._entries)

    def by_category(self, category: str) -> list[dict[str, Any]]:
        return [b for b in self._entries if b.get("category") == category]

    def favorites(self) -> list[dict[str, Any]]:
        return [b for b in self._entries if b.get("favorite")]

    def search(self, query: str) -> list[dict[str, Any]]:
        q = query.lower()
        return [
            b for b in self._entries
            if q in b["url"].lower() or q in b.get("title", "").lower()
        ]

    def export_json(self, dest: Path) -> None:
        with open(dest, "w", encoding="utf-8") as fh:
            json.dump(self._entries, fh, indent=2)

    def import_json(self, src: Path) -> int:
        with open(src, "r", encoding="utf-8") as fh:
            imported = json.load(fh)
        count = 0
        for item in imported:
            url = item.get("url")
            if url and not self.is_bookmarked(url):
                item.setdefault("category", "Imported")
                self._entries.append(item)
                count += 1
        self.save()
        return count
