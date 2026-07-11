"""
plugins/example_plugin.py
A minimal example plugin. Copy this file, rename it, and edit `register`
to add your own commands, shortcuts, or settings. Any .py file dropped
into plugins/ is auto-loaded on startup by plugin_loader.py.
"""

from __future__ import annotations

from commands import Command


def register(browser) -> None:
    """Called once at startup with the fully-initialized Browser instance."""

    def open_anthropic() -> None:
        browser.navigate("https://www.anthropic.com")

    browser.registry.register(
        Command(
            id="plugin_example_open_anthropic",
            title="Example Plugin: Open Anthropic.com",
            callback=open_anthropic,
            category="Plugins",
            keywords=["example", "demo"],
        )
    )
