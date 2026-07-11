"""
tabs.py
Manages browser tabs without a permanent visible tab bar. Tabs live in a
QStackedWidget; switching, closing, pinning, and duplicating all happen
through the tab popup (ui/tab_popup.py) or keyboard shortcuts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtWidgets import QStackedWidget

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
except ImportError:  # pragma: no cover
    QWebEngineView = None  # type: ignore


@dataclass
class TabInfo:
    """Lightweight metadata mirror of a live tab, used for popups/session save."""
    view: "QWebEngineView"
    pinned: bool = False
    audio: bool = False

    @property
    def title(self) -> str:
        return self.view.title() or "New Tab"

    @property
    def url(self) -> str:
        return self.view.url().toString()


class TabManager(QObject):
    """Owns the stacked widget of QWebEngineViews and tab lifecycle."""

    tab_added = Signal(int)
    tab_closed = Signal(int)
    active_tab_changed = Signal(int)
    tab_title_changed = Signal(int)

    def __init__(self, on_new_view: Callable[[], "QWebEngineView"],
                 home_html_provider: Callable[[], str] | None = None) -> None:
        super().__init__()
        self.stack = QStackedWidget()
        self._on_new_view = on_new_view
        self._home_html_provider = home_html_provider
        self.tabs: list[TabInfo] = []
        self._closed_stack: list[str] = []  # URLs of recently closed tabs, for restore

    # -- lifecycle -----------------------------------------------------
    def new_tab(self, url: str = "void://home", pinned: bool = False, focus: bool = True) -> int:
        view = self._on_new_view()
        if url == "void://home" and self._home_html_provider is not None:
            view.setHtml(self._home_html_provider(), QUrl("void://home"))
        elif url:
            view.setUrl(QUrl(url))
        info = TabInfo(view=view, pinned=pinned)
        self.tabs.append(info)
        index = len(self.tabs) - 1
        self.stack.addWidget(view)
        view.titleChanged.connect(lambda _t, i=index: self.tab_title_changed.emit(i))
        self.tab_added.emit(index)
        if focus:
            self.set_active(index)
        return index

    def close_tab(self, index: int) -> None:
        if not (0 <= index < len(self.tabs)):
            return
        info = self.tabs.pop(index)
        if not info.url.startswith("void://"):
            self._closed_stack.append(info.url)
        self.stack.removeWidget(info.view)
        info.view.deleteLater()
        self.tab_closed.emit(index)
        if self.tabs:
            new_index = min(index, len(self.tabs) - 1)
            self.set_active(new_index)

    def close_others(self, keep_index: int) -> None:
        for i in reversed(range(len(self.tabs))):
            if i != keep_index:
                self.close_tab(i)

    def duplicate_tab(self, index: int) -> int:
        if not (0 <= index < len(self.tabs)):
            return -1
        url = self.tabs[index].url
        return self.new_tab(url=url)

    def restore_last_closed(self) -> int:
        if not self._closed_stack:
            return -1
        url = self._closed_stack.pop()
        return self.new_tab(url=url)

    def pin_tab(self, index: int, pinned: bool = True) -> None:
        if 0 <= index < len(self.tabs):
            self.tabs[index].pinned = pinned

    def move_tab(self, from_index: int, to_index: int) -> None:
        if 0 <= from_index < len(self.tabs) and 0 <= to_index < len(self.tabs):
            info = self.tabs.pop(from_index)
            self.tabs.insert(to_index, info)

    # -- navigation ------------------------------------------------------
    def set_active(self, index: int) -> None:
        if 0 <= index < len(self.tabs):
            self.stack.setCurrentIndex(index)
            self.active_tab_changed.emit(index)

    def active_index(self) -> int:
        return self.stack.currentIndex()

    def active_view(self) -> "QWebEngineView | None":
        idx = self.active_index()
        if 0 <= idx < len(self.tabs):
            return self.tabs[idx].view
        return None

    def next_tab(self) -> None:
        if self.tabs:
            self.set_active((self.active_index() + 1) % len(self.tabs))

    def prev_tab(self) -> None:
        if self.tabs:
            self.set_active((self.active_index() - 1) % len(self.tabs))

    def count(self) -> int:
        return len(self.tabs)

    def recently_closed(self, limit: int = 6) -> list[str]:
        return list(reversed(self._closed_stack[-limit:]))
