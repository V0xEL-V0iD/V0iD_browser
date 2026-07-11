"""
themes.py
Loads JSON theme definitions from themes/*.json and turns them into Qt
Style Sheets (QSS) applied at runtime. Switching themes never requires
restarting the browser -- widgets listen for `theme_changed` and re-poll
the stylesheet.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal

ROOT_DIR = Path(__file__).resolve().parent
THEMES_DIR = ROOT_DIR / "themes"


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    """Convert '#rrggbb' to a Qt-QSS-safe 'rgba(r, g, b, a)' string.

    Qt's stylesheet engine expects #AARRGGBB (alpha first) rather than the
    CSS convention of #RRGGBBAA, so appending an alpha suffix to a hex code
    would be silently misparsed. rgba() is unambiguous across Qt versions.
    """
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return hex_color
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"


class ThemeManager(QObject):
    """Loads a theme JSON file and exposes it as QSS + raw values."""

    theme_changed = Signal(str)

    def __init__(self, theme_name: str = "void") -> None:
        super().__init__()
        self._name = theme_name
        self._data: dict[str, Any] = {}
        self.load(theme_name)

    # -- discovery -----------------------------------------------------
    @staticmethod
    def available_themes() -> list[str]:
        if not THEMES_DIR.exists():
            return []
        return sorted(p.stem for p in THEMES_DIR.glob("*.json"))

    # -- loading ---------------------------------------------------------
    def load(self, theme_name: str) -> None:
        path = THEMES_DIR / f"{theme_name}.json"
        if not path.exists():
            path = THEMES_DIR / "void.json"
            theme_name = "void"
        with open(path, "r", encoding="utf-8") as fh:
            self._data = json.load(fh)
        self._name = theme_name
        self.theme_changed.emit(theme_name)

    def switch(self, theme_name: str) -> None:
        self.load(theme_name)

    # -- accessors ---------------------------------------------------------
    def value(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    @property
    def name(self) -> str:
        return self._data.get("name", self._name)

    def as_dict(self) -> dict[str, Any]:
        return dict(self._data)

    # -- QSS generation --------------------------------------------------
    def stylesheet(self) -> str:
        """Build a global QSS string from the active theme's JSON values."""
        d = self._data
        bg = d.get("background", "#0d0d12")
        bg_alt = d.get("background_alt", "#15151d")
        fg = d.get("foreground", "#e6e6f0")
        fg_dim = d.get("foreground_dim", "#8a8a9a")
        accent = d.get("accent", "#9d7bff")
        accent_alt = d.get("accent_alt", "#ff7bd4")
        border_color = d.get("border_color", "#2a2a38")
        border_width = d.get("border_width", 1)
        border_radius = d.get("border_radius", 12)
        font_family = d.get("font_family", "JetBrainsMono Nerd Font")
        font_size = d.get("font_size", 14)
        padding = d.get("padding", 10)

        return f"""
        * {{
            font-family: "{font_family}";
            font-size: {font_size}px;
            color: {fg};
        }}
        QWidget#floatingPopup {{
            background-color: {bg};
            border: {border_width}px solid {border_color};
            border-radius: {border_radius}px;
        }}
        QWidget {{
            background-color: transparent;
        }}
        QLineEdit {{
            background-color: {bg_alt};
            border: {border_width}px solid {border_color};
            border-radius: {max(border_radius - 4, 4)}px;
            padding: {padding // 2}px {padding}px;
            color: {fg};
            selection-background-color: {accent};
        }}
        QListWidget {{
            background-color: transparent;
            border: none;
            outline: none;
            padding: 4px;
        }}
        QListWidget::item {{
            background-color: {bg_alt};
            padding: {padding // 2}px {padding}px;
            border-radius: {max(border_radius - 6, 4)}px;
            margin-bottom: 4px;
            color: {fg};
        }}
        QListWidget::item:selected {{
            background-color: {accent};
            color: {bg};
        }}
        QListWidget::item:hover {{
            background-color: {_hex_to_rgba(accent, 0.2)};
        }}
        QLabel#dimLabel {{
            color: {fg_dim};
        }}
        QLabel#accentLabel {{
            color: {accent};
        }}
        QPushButton {{
            background-color: {bg_alt};
            border: {border_width}px solid {border_color};
            border-radius: {max(border_radius - 6, 4)}px;
            padding: {padding // 2}px {padding}px;
            color: {fg};
        }}
        QPushButton:hover {{
            background-color: {accent};
            color: {bg};
        }}
        QComboBox {{
            background-color: {bg_alt};
            border: {border_width}px solid {border_color};
            border-radius: {max(border_radius - 6, 4)}px;
            padding: {padding // 2}px {padding}px;
            color: {fg};
        }}
        QComboBox:hover {{
            border: {border_width}px solid {accent};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 22px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {bg_alt};
            border: {border_width}px solid {border_color};
            border-radius: {max(border_radius - 6, 4)}px;
            outline: none;
            padding: 4px;
            color: {fg};
            selection-background-color: {accent};
            selection-color: {bg};
        }}
        QMenu {{
            background-color: {bg_alt};
            border: {border_width}px solid {border_color};
            border-radius: {max(border_radius - 6, 4)}px;
            padding: 4px;
            color: {fg};
        }}
        QMenu::item {{
            padding: {padding // 2}px {padding}px;
            border-radius: {max(border_radius - 8, 3)}px;
        }}
        QMenu::item:selected {{
            background-color: {accent};
            color: {bg};
        }}
        QMenu::separator {{
            height: 1px;
            background: {border_color};
            margin: 4px 6px;
        }}
        QCheckBox {{
            color: {fg};
            spacing: 8px;
        }}
        QCheckBox::indicator {{
            width: 14px;
            height: 14px;
            border: {border_width}px solid {border_color};
            border-radius: 4px;
            background-color: {bg_alt};
        }}
        QCheckBox::indicator:checked {{
            background-color: {accent};
            border: {border_width}px solid {accent};
        }}
        QScrollBar:vertical {{
            background: transparent;
            width: 8px;
        }}
        QScrollBar::handle:vertical {{
            background: {border_color};
            border-radius: 4px;
        }}
        QProgressBar {{
            background-color: {bg_alt};
            border: 1px solid {border_color};
            border-radius: 6px;
            text-align: center;
            color: {fg};
        }}
        QProgressBar::chunk {{
            background-color: {accent};
            border-radius: 6px;
        }}
        """
