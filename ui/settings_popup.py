"""
ui/settings_popup.py
A simple settings popup for the most commonly toggled preferences.
Everything here reads/writes straight through to config/settings.json
via the Settings manager, so the JSON file remains the single source
of truth.
"""

from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import (
    QLabel, QComboBox, QCheckBox, QFormLayout, QWidget, QLineEdit
)

from popup import FloatingPopup
from settings import Settings
from themes import ThemeManager
from search import SearchManager


class SettingsPopup(FloatingPopup):
    def __init__(self, parent, settings: Settings, theme_manager: ThemeManager,
                 search_manager: SearchManager, on_theme_changed: Callable[[str], None],
                 on_dark_mode_toggle: Callable[[bool], None],
                 on_force_dark_web_toggle: Callable[[], None]) -> None:
        super().__init__(parent, width_ratio=0.45, height=500, anchor="center")
        self.settings = settings
        self.theme_manager = theme_manager
        self.search_manager = search_manager
        self.on_theme_changed = on_theme_changed
        self.on_dark_mode_toggle = on_dark_mode_toggle
        self.on_force_dark_web_toggle = on_force_dark_web_toggle

        title = QLabel("Settings")
        title.setObjectName("accentLabel")
        self.layout_.addWidget(title)

        form_host = QWidget()
        form = QFormLayout(form_host)

        self.dark_mode_check = QCheckBox("Dark mode")
        self.dark_mode_check.setChecked(bool(self.theme_manager.value("dark", True)))
        self.dark_mode_check.toggled.connect(self._toggle_dark_mode)
        form.addRow(self.dark_mode_check)

        self.force_dark_web_check = QCheckBox("Force dark mode on websites")
        self.force_dark_web_check.setChecked(bool(self.settings.get("force_dark_web_content", True)))
        self.force_dark_web_check.toggled.connect(self._toggle_force_dark_web)
        form.addRow(self.force_dark_web_check)

        self.theme_box = QComboBox()
        self.theme_box.addItems(ThemeManager.available_themes())
        self.theme_box.setCurrentText(self.settings.active_theme)
        self.theme_box.currentTextChanged.connect(self._change_theme)
        form.addRow("Theme", self.theme_box)

        self.engine_box = QComboBox()
        engines = self.search_manager.engines()
        self.engine_box.addItems(list(engines.keys()))
        self.engine_box.setCurrentText(self.search_manager.default_engine)
        self.engine_box.currentTextChanged.connect(self.search_manager.set_default_engine)
        form.addRow("Search engine", self.engine_box)

        self.homepage_edit = QLineEdit(self.settings.get("homepage", "void://home"))
        self.homepage_edit.editingFinished.connect(
            lambda: self.settings.set("homepage", self.homepage_edit.text())
        )
        form.addRow("Homepage", self.homepage_edit)

        self.vim_check = QCheckBox("Enable Vim mode")
        self.vim_check.setChecked(bool(self.settings.get("vim_mode", True)))
        self.vim_check.toggled.connect(lambda v: self.settings.set("vim_mode", v))
        form.addRow(self.vim_check)

        self.smooth_scroll_check = QCheckBox("Smooth scrolling")
        self.smooth_scroll_check.setChecked(bool(self.settings.get("smooth_scrolling", True)))
        self.smooth_scroll_check.toggled.connect(lambda v: self.settings.set("smooth_scrolling", v))
        form.addRow(self.smooth_scroll_check)

        self.animations_check = QCheckBox("Animations")
        self.animations_check.setChecked(bool(self.settings.get("animations", True)))
        self.animations_check.toggled.connect(lambda v: self.settings.set("animations", v))
        form.addRow(self.animations_check)

        self.dnt_check = QCheckBox("Send Do Not Track")
        self.dnt_check.setChecked(bool(self.settings.get("privacy.do_not_track", True)))
        self.dnt_check.toggled.connect(lambda v: self.settings.set("privacy.do_not_track", v))
        form.addRow(self.dnt_check)

        self.layout_.addWidget(form_host)

    def _toggle_force_dark_web(self, checked: bool) -> None:
        self.settings.set("force_dark_web_content", checked)
        self.on_force_dark_web_toggle()

    def _toggle_dark_mode(self, checked: bool) -> None:
        self.on_dark_mode_toggle(checked)
        self.on_force_dark_web_toggle()
        # The active theme may have changed as a result (e.g. switched to "light").
        self.theme_box.blockSignals(True)
        self.theme_box.setCurrentText(self.settings.active_theme)
        self.theme_box.blockSignals(False)

    def _change_theme(self, theme_name: str) -> None:
        self.settings.set("active_theme", theme_name)
        self.theme_manager.switch(theme_name)
        if self.theme_manager.value("dark", True):
            self.settings.set("dark_theme", theme_name)
        self.on_theme_changed(theme_name)
        self.dark_mode_check.blockSignals(True)
        self.dark_mode_check.setChecked(bool(self.theme_manager.value("dark", True)))
        self.dark_mode_check.blockSignals(False)

    def open(self) -> None:
        # Resync every field in case settings changed elsewhere (command palette, etc).
        self.dark_mode_check.blockSignals(True)
        self.dark_mode_check.setChecked(bool(self.theme_manager.value("dark", True)))
        self.dark_mode_check.blockSignals(False)
        self.force_dark_web_check.blockSignals(True)
        self.force_dark_web_check.setChecked(bool(self.settings.get("force_dark_web_content", True)))
        self.force_dark_web_check.blockSignals(False)
        self.theme_box.blockSignals(True)
        self.theme_box.setCurrentText(self.settings.active_theme)
        self.theme_box.blockSignals(False)
        self.show_animated()
