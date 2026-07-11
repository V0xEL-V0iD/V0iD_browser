"""
search.py
Manages search engines defined in config/search.json and turns raw
address-bar input into either a direct URL or a search-engine query URL.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import quote_plus

ROOT_DIR = Path(__file__).resolve().parent
SEARCH_PATH = ROOT_DIR / "config" / "search.json"

# A loose check for "looks like a URL / domain" vs. "looks like a search query".
_URL_RE = re.compile(
    r"^(https?://|about:|void://|file://)"
    r"|^[\w-]+(\.[\w-]+)+(:\d+)?(/.*)?$"
    r"|^localhost(:\d+)?(/.*)?$",
    re.IGNORECASE,
)


class SearchManager:
    """Resolves user input to a navigable URL and manages search engines."""

    def __init__(self, path: Path = SEARCH_PATH) -> None:
        self.path = path
        self._data: dict = {}
        self.load()

    def load(self) -> None:
        with open(self.path, "r", encoding="utf-8") as fh:
            self._data = json.load(fh)

    def save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=4)

    @property
    def default_engine(self) -> str:
        return self._data.get("default", "duckduckgo")

    def set_default_engine(self, engine_id: str) -> None:
        if engine_id in self._data.get("engines", {}):
            self._data["default"] = engine_id
            self.save()

    def engines(self) -> dict:
        return self._data.get("engines", {})

    def add_engine(self, engine_id: str, name: str, url: str, suggest_url: str = "") -> None:
        self._data.setdefault("engines", {})[engine_id] = {
            "name": name,
            "url": url,
            "suggest_url": suggest_url,
        }
        self.save()

    def query_url(self, query: str, engine_id: str | None = None) -> str:
        """Build a search-engine URL for a free-text query."""
        engine_id = engine_id or self.default_engine
        engine = self.engines().get(engine_id) or next(iter(self.engines().values()))
        return engine["url"].format(query=quote_plus(query))

    @staticmethod
    def looks_like_url(text: str) -> bool:
        text = text.strip()
        if not text:
            return False
        if " " in text:
            return False
        return bool(_URL_RE.match(text))

    def resolve(self, text: str, engine_id: str | None = None) -> str:
        """Turn raw address-bar text into a fully qualified URL to load."""
        text = text.strip()
        if not text:
            return "void://home"
        if self.looks_like_url(text):
            if not re.match(r"^\w+://", text):
                return f"https://{text}"
            return text
        return self.query_url(text, engine_id)
