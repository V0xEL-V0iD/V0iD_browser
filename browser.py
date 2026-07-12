"""
browser.py
The application glue layer. Wires together settings, themes, tabs,
history/bookmarks/downloads, the command registry, keyboard shortcuts,
every floating popup, and a lightweight Vim navigation mode.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QUrl, QObject
from PySide6.QtWidgets import QApplication

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
except ImportError:  # pragma: no cover
    QWebEngineView = None  # type: ignore
    QWebEngineProfile = None  # type: ignore
    QWebEngineSettings = None  # type: ignore

from settings import Settings
from themes import ThemeManager
from shortcuts import ShortcutManager
from search import SearchManager
from history import HistoryManager
from bookmarks import BookmarkManager
from downloads import DownloadManager
from workspace import WorkspaceManager
from tabs import TabManager
from commands import Command, CommandRegistry
from window import MainWindow

from ui.url_popup import UrlPopup
from ui.launcher import Launcher
from ui.command_palette import CommandPalette
from ui.tab_popup import TabPopup
from ui.bookmark_popup import BookmarkPopup
from ui.history_popup import HistoryPopup
from ui.downloads_popup import DownloadsPopup
from ui.settings_popup import SettingsPopup


class VimMode(QObject):
    """A minimal Vim-style keyboard navigation layer for the active web view.

    Installed as an event filter on the main window; only intercepts keys
    when vim mode is enabled and no popup/input field currently has focus.
    """

    def __init__(self, browser: "Browser") -> None:
        super().__init__(browser.window)
        self.browser = browser
        self._pending = ""  # for multi-key sequences like 'gg' and 'yy'

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        if event.type() != event.Type.KeyPress:
            return False
        if not self.browser.settings.get("vim_mode", True):
            return False
        focus_widget = QApplication.focusWidget()
        # Don't hijack typing inside line edits or the web view's own text inputs.
        if focus_widget is not None and focus_widget.metaObject().className() == "QLineEdit":
            return False

        key = event.text()
        if not key or event.modifiers() not in (Qt.KeyboardModifier.NoModifier, Qt.KeyboardModifier.ShiftModifier):
            self._pending = ""
            return False

        view = self.browser.tab_manager.active_view()
        if view is None:
            return False

        combo = self._pending + key
        actions = self.browser.vim_actions
        if combo in actions:
            actions[combo]()
            self._pending = ""
            return True
        if any(k.startswith(combo) for k in actions if len(k) > 1):
            self._pending = combo
            return True
        self._pending = ""
        return False


class Browser:
    """Owns every manager/popup and boots the application."""

    def __init__(self, app: QApplication) -> None:
        self.app = app
        self.settings = Settings()
        self.theme_manager = ThemeManager(self.settings.active_theme)
        self.search_manager = SearchManager()
        self.history_manager = HistoryManager()
        self.bookmark_manager = BookmarkManager()
        self.download_manager = DownloadManager()
        self.workspace_manager = WorkspaceManager()
        self.registry = CommandRegistry()

        self.window = MainWindow()
        self.shortcuts = ShortcutManager(self.window)

        self.profile = QWebEngineProfile.defaultProfile() if QWebEngineProfile else None
        if self.profile is not None:
            self.profile.downloadRequested.connect(self.download_manager.handle_download)
            self.profile.setHttpAcceptLanguage("en-US,en")

        self.tab_manager = TabManager(self._create_web_view, home_html_provider=self._home_html)
        self.window.attach_tab_manager(self.tab_manager)
        self.tab_manager.active_tab_changed.connect(lambda _i: self._sync_window_title())
        self.tab_manager.tab_title_changed.connect(lambda _i: self._sync_window_title())

        self._build_popups()
        self._register_commands()
        self._bind_shortcuts()
        self._apply_theme(self.theme_manager.name)
        self._apply_force_dark_mode()
        self.theme_manager.theme_changed.connect(lambda _n: self._apply_theme(self.theme_manager.name))
        self.theme_manager.theme_changed.connect(lambda _n: self._apply_force_dark_mode())

        self.vim_mode = VimMode(self)
        self.vim_actions = self._build_vim_actions()
        self.window.installEventFilter(self.vim_mode)

        self._restore_or_home()
        self.app.aboutToQuit.connect(self._save_session)

        from plugin_loader import load_plugins
        loaded = load_plugins(self)
        if loaded:
            print(f"[VoidBrowser] Loaded plugins: {', '.join(loaded)}")

    # -- web view factory --------------------------------------------------
    def _create_web_view(self) -> "QWebEngineView":
        view = QWebEngineView()
        if self.profile is not None:
            from PySide6.QtWebEngineCore import QWebEnginePage
            page = QWebEnginePage(self.profile, view)
            view.setPage(page)
            if QWebEngineSettings is not None:
                attr = getattr(QWebEngineSettings.WebAttribute, "ForceDarkMode", None)
                if attr is not None:
                    is_dark = bool(self.settings.get("force_dark_web_content", True)) and \
                        bool(self.theme_manager.value("dark", True))
                    page.settings().setAttribute(attr, is_dark)

                fs_attr = getattr(QWebEngineSettings.WebAttribute, "FullScreenSupportEnabled", None)
                if fs_attr is not None:
                    page.settings().setAttribute(fs_attr, True)

        
        view.urlChanged.connect(lambda url, v=view: self._on_url_changed(v, url))
        return view

    def _on_url_changed(self, view, url: QUrl) -> None:
        url_str = url.toString()
        if url_str and not url_str.startswith("void://"):
            self.history_manager.visit(url_str, view.title())

    def _sync_window_title(self) -> None:
        view = self.tab_manager.active_view()
        if view is not None:
            title = view.title() or "VoidBrowser"
            self.window.setWindowTitle(f"{title} — VoidBrowser")

    # -- homepage ------------------------------------------------------
    def _home_html(self) -> str:
        pinned = self.bookmark_manager.by_category("Pinned")
        recent = self.history_manager.recent(6)
        frequent = self.history_manager.most_visited(6)
        bookmarks = self.bookmark_manager.favorites() or self.bookmark_manager.all()[:6]
        closed = self.tab_manager.recently_closed(6)
        theme = self.theme_manager.as_dict()
        return self.window.build_homepage_html(theme, pinned, recent, frequent, bookmarks, closed)

    def go_home(self) -> None:
        view = self.tab_manager.active_view()
        if view is not None:
            view.setHtml(self._home_html(), QUrl("void://home"))

    # -- theming ---------------------------------------------------------
    def _apply_theme(self, theme_name: str) -> None:
        self.app.setStyleSheet(self.theme_manager.stylesheet())

    def _apply_force_dark_mode(self) -> None:
        """Force web page content (not just browser chrome) into dark mode
        when a dark theme is active, using Chromium's built-in dark-mode
        renderer. Falls back to a no-op on Qt versions that lack the
        attribute (added in Qt 6.7's QWebEngineSettings)."""
        if self.profile is None or QWebEngineSettings is None:
            return
        attr = getattr(QWebEngineSettings.WebAttribute, "ForceDarkMode", None)
        if attr is None:
            return
        is_dark = bool(self.settings.get("force_dark_web_content", True)) and \
            bool(self.theme_manager.value("dark", True))
        self.profile.settings().setAttribute(attr, is_dark)
        # Some Qt builds snapshot settings per-page at creation time rather
        # than reading the profile live, so re-apply to every open tab too.
        for tab in self.tab_manager.tabs:
            page = tab.view.page()
            if page is not None:
                page.settings().setAttribute(attr, is_dark)

    # -- popups ------------------------------------------------------------
    def _build_popups(self) -> None:
        self.url_popup = UrlPopup(
            self.window, self.history_manager, self.bookmark_manager,
            self.search_manager, self.navigate,
        )
        self.launcher = Launcher(self.window, self.registry)
        self.command_palette = CommandPalette(self.window, self.registry)
        self.tab_popup = TabPopup(self.window, self.tab_manager)
        self.bookmark_popup = BookmarkPopup(self.window, self.bookmark_manager, self.navigate)
        self.history_popup = HistoryPopup(self.window, self.history_manager, self.navigate)
        self.downloads_popup = DownloadsPopup(self.window, self.download_manager)
        self.settings_popup = SettingsPopup(
            self.window, self.settings, self.theme_manager, self.search_manager,
            self._apply_theme, self._set_dark_mode, self._apply_force_dark_mode,
        )

    # -- navigation --------------------------------------------------------
    def navigate(self, url: str) -> None:
        view = self.tab_manager.active_view()
        if view is None:
            self.tab_manager.new_tab(url=url)
            return
        if url == "void://home":
            view.setHtml(self._home_html(), QUrl("void://home"))
        else:
            view.setUrl(QUrl(url))

    # -- commands ------------------------------------------------------
    def _register_commands(self) -> None:
        def cmd(id_, title, callback, category="General", shortcut_key=""):
            shortcut = self.shortcuts.key_for(shortcut_key) if shortcut_key else ""
            self.registry.register(Command(id=id_, title=title, callback=callback,
                                            category=category, shortcut=shortcut or ""))

        cmd("new_tab", "New Tab", lambda: self.tab_manager.new_tab(url=self.settings.get("homepage", "void://home")),
            "Tabs", "new_tab")
        cmd("close_tab", "Close Tab", lambda: self.tab_manager.close_tab(self.tab_manager.active_index()),
            "Tabs", "close_tab")
        cmd("duplicate_tab", "Duplicate Tab", lambda: self.tab_manager.duplicate_tab(self.tab_manager.active_index()),
            "Tabs", "duplicate_tab")
        cmd("restore_tab", "Restore Closed Tab", self.tab_manager.restore_last_closed, "Tabs", "restore_tab")
        cmd("close_others", "Close Other Tabs", lambda: self.tab_manager.close_others(self.tab_manager.active_index()), "Tabs")
        cmd("pin_tab", "Pin/Unpin Current Tab", self._toggle_pin_active_tab, "Tabs")

        cmd("open_url", "Open URL", self.url_popup.open, "Navigation", "url_popup")
        cmd("reload", "Reload", self._reload, "Navigation", "reload")
        cmd("hard_reload", "Hard Reload", self._hard_reload, "Navigation", "hard_reload")
        cmd("go_back", "Back", self._go_back, "Navigation", "back")
        cmd("go_forward", "Forward", self._go_forward, "Navigation", "forward")
        cmd("go_home", "Go Home", self.go_home, "Navigation")

        cmd("open_bookmarks", "Bookmarks", self.bookmark_popup.open, "Data", "bookmarks")
        cmd("add_bookmark", "Bookmark This Page", self._bookmark_current, "Data", "add_bookmark")
        cmd("open_history", "History", self.history_popup.open, "Data", "history")
        cmd("clear_history", "Clear All History", self.history_manager.clear, "Data")
        cmd("open_downloads", "Downloads", self.downloads_popup.open, "Data", "downloads")
        cmd("import_bookmarks", "Import Bookmarks", self._import_bookmarks, "Data")
        cmd("export_bookmarks", "Export Bookmarks", self._export_bookmarks, "Data")

        cmd("open_settings", "Settings", self.settings_popup.open, "App", "settings")
        cmd("open_launcher", "Launcher", self.launcher.open, "App", "launcher")
        cmd("open_command_palette", "Command Palette", self.command_palette.open, "App", "command_palette")
        cmd("open_tab_popup", "Switch Tab", self.tab_popup.open, "Tabs", "tab_popup")
        cmd("toggle_dark_mode", "Toggle Dark Mode", self._toggle_dark_mode, "App", "toggle_dark_mode")
        cmd("toggle_vim_mode", "Toggle Vim Mode", self._toggle_vim_mode, "App", "toggle_vim_mode")
        cmd("toggle_incognito", "Toggle Incognito Mode", self._toggle_incognito, "Privacy", "toggle_incognito")
        cmd("clear_cache", "Clear Cache", self._clear_cache, "Privacy")
        cmd("dev_tools", "Toggle Developer Tools", self._toggle_devtools, "App", "dev_tools")
        cmd("fullscreen", "Toggle Fullscreen", self._toggle_fullscreen, "App", "fullscreen")
        cmd("quit", "Quit VoidBrowser", self.app.quit, "App", "quit")

        for theme_name in ThemeManager.available_themes():
            cmd(f"theme_{theme_name}", f"Theme: {theme_name.title()}",
                lambda t=theme_name: self._set_theme(t), "Themes")

    # -- command implementations --------------------------------------------
    def _reload(self) -> None:
        view = self.tab_manager.active_view()
        if view:
            view.reload()

    def _hard_reload(self) -> None:
        view = self.tab_manager.active_view()
        if view:
            view.page().triggerAction(view.page().WebAction.ReloadAndBypassCache)

    def _go_back(self) -> None:
        view = self.tab_manager.active_view()
        if view:
            view.back()

    def _go_forward(self) -> None:
        view = self.tab_manager.active_view()
        if view:
            view.forward()

    def _toggle_pin_active_tab(self) -> None:
        idx = self.tab_manager.active_index()
        if 0 <= idx < len(self.tab_manager.tabs):
            tab = self.tab_manager.tabs[idx]
            self.tab_manager.pin_tab(idx, not tab.pinned)

    def _bookmark_current(self) -> None:
        view = self.tab_manager.active_view()
        if view:
            self.bookmark_manager.add(view.url().toString(), view.title(), category="Favorites", favorite=True)

    def _import_bookmarks(self) -> None:
        from pathlib import Path
        path = Path.home() / "voidbrowser_bookmarks_import.json"
        if path.exists():
            self.bookmark_manager.import_json(path)

    def _export_bookmarks(self) -> None:
        from pathlib import Path
        path = Path.home() / "voidbrowser_bookmarks_export.json"
        self.bookmark_manager.export_json(path)

    def _set_dark_mode(self, dark: bool) -> None:
        """Switch between the light theme and whichever dark theme was last active."""
        currently_dark = bool(self.theme_manager.value("dark", True))
        if dark:
            self._set_theme(self.settings.get("dark_theme", "void"))
        else:
            if currently_dark:
                self.settings.set("dark_theme", self.settings.active_theme)
            self._set_theme("light")

    def _toggle_dark_mode(self) -> None:
        self._set_dark_mode(not bool(self.theme_manager.value("dark", True)))

    def _set_theme(self, theme_name: str) -> None:
        self.settings.set("active_theme", theme_name)
        self.theme_manager.switch(theme_name)

    def _toggle_vim_mode(self) -> None:
        current = bool(self.settings.get("vim_mode", True))
        self.settings.set("vim_mode", not current)

    def _toggle_incognito(self) -> None:
        current = bool(self.settings.get("privacy.incognito_default", False))
        self.settings.set("privacy.incognito_default", not current)

    def _clear_cache(self) -> None:
        if self.profile is not None:
            self.profile.clearHttpCache()

    def _toggle_devtools(self) -> None:
        view = self.tab_manager.active_view()
        if view is None:
            return
        page = view.page()
        if getattr(self, "_devtools_view", None) is None:
            self._devtools_view = QWebEngineView()
            page.setDevToolsPage(self._devtools_view.page())
            self._devtools_view.setWindowTitle("VoidBrowser DevTools")
            self._devtools_view.resize(1000, 700)
        self._devtools_view.show()

    def _toggle_fullscreen(self) -> None:
        if self.window.isFullScreen():
            self.window.showNormal()
        else:
            self.window.showFullScreen()

    def _on_page_fullscreen_requested(self, request) -> None:
        """Answer a web page's request to go fullscreen (e.g. YouTube's
        own fullscreen button), which Qt WebEngine otherwise silently
        refuses unless something explicitly accepts it."""
        request.accept()
        if request.toggleOn():
            self._was_maximized_before_fullscreen = self.window.isMaximized()
            self.window.showFullScreen()
        else:
            if getattr(self, "_was_maximized_before_fullscreen", False):
                self.window.showMaximized()
            else:
                self.window.showNormal()

    # -- vim mode --------------------------------------------------------
    def _build_vim_actions(self) -> dict:
        def scroll(dy: int):
            view = self.tab_manager.active_view()
            if view:
                view.page().runJavaScript(f"window.scrollBy(0, {dy});")

        def top():
            view = self.tab_manager.active_view()
            if view:
                view.page().runJavaScript("window.scrollTo(0, 0);")

        def bottom():
            view = self.tab_manager.active_view()
            if view:
                view.page().runJavaScript("window.scrollTo(0, document.body.scrollHeight);")

        def yank_url():
            view = self.tab_manager.active_view()
            if view:
                QApplication.clipboard().setText(view.url().toString())

        def paste_url():
            text = QApplication.clipboard().text().strip()
            if text:
                self.navigate(self.search_manager.resolve(text))

        v = self.shortcuts.vim_bindings()
        return {
            v.get("scroll_down", "j"): lambda: scroll(80),
            v.get("scroll_up", "k"): lambda: scroll(-80),
            v.get("back", "h"): self._go_back,
            v.get("forward", "l"): self._go_forward,
            v.get("top", "gg"): top,
            v.get("bottom", "G"): bottom,
            v.get("yank_url", "yy"): yank_url,
            v.get("paste_url", "p"): paste_url,
            v.get("url_popup", "o"): self.url_popup.open,
            v.get("tab_popup", "t"): self.tab_popup.open,
            v.get("bookmarks", "b"): self.bookmark_popup.open,
            v.get("reload", "r"): self._reload,
        }

    # -- shortcut binding --------------------------------------------------
    def _bind_shortcuts(self) -> None:
        binding_map = {
            "url_popup": self.url_popup.open,
            "launcher": self.launcher.open,
            "command_palette": self.command_palette.open,
            "tab_popup": self.tab_popup.open,
            "new_tab": lambda: self.tab_manager.new_tab(url=self.settings.get("homepage", "void://home")),
            "close_tab": lambda: self.tab_manager.close_tab(self.tab_manager.active_index()),
            "duplicate_tab": lambda: self.tab_manager.duplicate_tab(self.tab_manager.active_index()),
            "restore_tab": self.tab_manager.restore_last_closed,
            "next_tab": self.tab_manager.next_tab,
            "prev_tab": self.tab_manager.prev_tab,
            "reload": self._reload,
            "hard_reload": self._hard_reload,
            "bookmarks": self.bookmark_popup.open,
            "add_bookmark": self._bookmark_current,
            "history": self.history_popup.open,
            "downloads": self.downloads_popup.open,
            "settings": self.settings_popup.open,
            "dev_tools": self._toggle_devtools,
            "fullscreen": self._toggle_fullscreen,
            "quit": self.app.quit,
            "back": self._go_back,
            "forward": self._go_forward,
            "focus_home": self.go_home,
            "toggle_vim_mode": self._toggle_vim_mode,
            "toggle_dark_mode": self._toggle_dark_mode,
            "toggle_incognito": self._toggle_incognito,
        }
        for action, callback in binding_map.items():
            self.shortcuts.bind(action, callback)

    # -- session -------------------------------------------------------
    def _restore_or_home(self) -> None:
        workspace = self.workspace_manager.active_workspace_name
        if self.settings.get("restore_previous_session", True):
            tabs, active_index = self.workspace_manager.load_tabs(workspace)
        else:
            tabs, active_index = [], 0

        if not tabs:
            self.tab_manager.new_tab(url=self.settings.get("homepage", "void://home"))
        else:
            for t in tabs:
                self.tab_manager.new_tab(url=t.get("url", "void://home"), pinned=t.get("pinned", False), focus=False)
            self.tab_manager.set_active(min(active_index, self.tab_manager.count() - 1))

    def _save_session(self) -> None:
        tabs = [
            {"url": t.url, "title": t.title, "pinned": t.pinned}
            for t in self.tab_manager.tabs
        ]
        self.workspace_manager.save_tabs(
            self.workspace_manager.active_workspace_name, tabs, self.tab_manager.active_index()
        )

    def show(self) -> None:
        self.window.show()
