"""
plugin_loader.py
Auto-discovers Python plugins in plugins/ and loads them. A plugin is any
.py file in plugins/ (excluding __init__.py and files starting with "_")
that defines a top-level `register(browser)` function. That function
receives the fully-initialized Browser instance and can:

    - browser.registry.register(Command(...))      # add commands
    - browser.launcher / browser.command_palette    # add launcher entries
    - browser.shortcuts.bind(action, callback)      # add shortcuts
    - browser.settings.set(...)                     # add/read settings

See plugins/example_plugin.py for a minimal working example.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
PLUGINS_DIR = ROOT_DIR / "plugins"


def load_plugins(browser) -> list[str]:
    """Import every plugin module in plugins/ and call its register(browser)."""
    loaded: list[str] = []
    if not PLUGINS_DIR.exists():
        return loaded

    for path in sorted(PLUGINS_DIR.glob("*.py")):
        if path.name.startswith("_"):
            continue
        module_name = f"voidbrowser_plugin_{path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
            register = getattr(module, "register", None)
            if callable(register):
                register(browser)
                loaded.append(path.stem)
        except Exception as exc:  # noqa: BLE001 - a broken plugin shouldn't crash the browser
            print(f"[VoidBrowser] Failed to load plugin '{path.stem}': {exc}", file=sys.stderr)

    return loaded
