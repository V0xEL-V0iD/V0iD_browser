"""
window.py
The main browser window. It has NO permanent toolbar or tab bar -- the
webpage (or the homepage) fills nearly the entire window. All chrome
(URL bar, launcher, tabs, bookmarks, history, downloads, settings)
lives in floating popups summoned by keyboard shortcuts.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget

from tabs import TabManager


class MainWindow(QMainWindow):
    """The frameless-feeling main window: just the web content, edge to edge."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("VoidBrowser")
        self.resize(1400, 900)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setCentralWidget(central)
        self._layout = layout

    def attach_tab_manager(self, tab_manager: TabManager) -> None:
        self._layout.addWidget(tab_manager.stack)

    # -- homepage ----------------------------------------------------------
    def build_homepage_html(self, theme: dict, pinned: list[dict], recent: list[dict],
                             frequent: list[dict], bookmarks: list[dict],
                             recently_closed: list[str]) -> str:
        """Generate the void://home page as static HTML/CSS, styled from the theme."""
        bg = theme.get("background", "#0d0d12")
        bg_alt = theme.get("background_alt", "#15151d")
        fg = theme.get("foreground", "#e6e6f0")
        fg_dim = theme.get("foreground_dim", "#8a8a9a")
        accent = theme.get("accent", "#9d7bff")
        radius = theme.get("border_radius", 14)
        font = theme.get("font_family", "sans-serif")

        def section(title: str, items: list, empty_msg: str) -> str:
            if not items:
                return f'<div class="section"><h2>{title}</h2><p class="dim">{empty_msg}</p></div>'
            rows = "".join(
                f'<div class="row"><span class="dot"></span>'
                f'<span class="row-title">{_esc(i.get("title") or i.get("url", i))}</span>'
                f'<span class="row-url dim">{_esc(i.get("url", i) if isinstance(i, dict) else i)}</span></div>'
                for i in items[:6]
            )
            return f'<div class="section"><h2>{title}</h2>{rows}</div>'

        def _esc(text: str) -> str:
            return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

        html = f"""
        <html>
        <head>
        <style>
            body {{
                margin: 0;
                background: {bg};
                color: {fg};
                font-family: {font}, sans-serif;
                display: flex;
                justify-content: center;
                padding: 60px 20px;
            }}
            .container {{ max-width: 900px; width: 100%; }}
            h1 {{
                font-size: 36px;
                color: {accent};
                text-align: center;
                margin-bottom: 4px;
            }}
            .subtitle {{ text-align: center; color: {fg_dim}; margin-bottom: 40px; }}
            .hint {{
                text-align: center;
                color: {fg_dim};
                margin-bottom: 40px;
                font-size: 13px;
            }}
            .hint kbd {{
                background: {bg_alt};
                padding: 2px 8px;
                border-radius: 6px;
                border: 1px solid {accent}55;
            }}
            .grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 24px;
            }}
            .section {{
                background: {bg_alt};
                border-radius: {radius}px;
                padding: 20px;
            }}
            .section h2 {{
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 1px;
                color: {accent};
                margin: 0 0 12px 0;
            }}
            .row {{
                display: flex;
                align-items: center;
                gap: 10px;
                padding: 6px 0;
                font-size: 14px;
            }}
            .dot {{
                width: 6px; height: 6px; border-radius: 50%;
                background: {accent};
                flex-shrink: 0;
            }}
            .row-title {{ flex-shrink: 0; }}
            .row-url {{
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
                font-size: 12px;
            }}
            .dim {{ color: {fg_dim}; }}
        </style>
        </head>
        <body>
            <div class="container">
                <h1>VoidBrowser</h1>
                <div class="subtitle">Keyboard-first. Minimal. Yours.</div>
                <div class="hint"><kbd>Ctrl+Space</kbd> search or go &nbsp;&nbsp;
                    <kbd>Ctrl+K</kbd> launcher &nbsp;&nbsp;
                    <kbd>Ctrl+Tab</kbd> tabs &nbsp;&nbsp;
                    <kbd>Ctrl+B</kbd> bookmarks</div>
                <div class="grid">
                    {section("Pinned", pinned, "No pinned sites yet.")}
                    {section("Frequently Visited", frequent, "Browse a bit and this fills in.")}
                    {section("Recent", recent, "No recent history yet.")}
                    {section("Bookmarks", bookmarks, "No bookmarks yet.")}
                    {section("Recently Closed", recently_closed, "Nothing closed recently.")}
                </div>
            </div>
        </body>
        </html>
        """
        return html
