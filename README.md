
# VoidBrowser

A keyboard-first web browser built with Python + PySide6 (Qt WebEngine),
inspired by Omarchy launchers, Zen Browser's floating UI, Vim workflows,
and modern Linux desktop aesthetics.

No permanent toolbar. No permanent tab bar. The page fills the window;
everything else — URL entry, tabs, bookmarks, history, downloads,
settings — lives in floating popups summoned by keyboard shortcuts.

## Requirements

- Python 3.11+ (3.13 recommended)
- PySide6 (Qt6 + Qt WebEngine)

```bash
pip install -r requirements.txt
```

> **Linux note:** Qt WebEngine needs a handful of system libraries
> (`libnss3`, `libxkbcommon0`, `libgl1`, etc). On Debian/Ubuntu-based
> distros (including Omarchy/Arch derivatives via your AUR helper of
> choice), install PySide6 through pip first and consult
> https://doc.qt.io/qtforpython-6/gettingstarted.html if the app fails
> to launch with a missing-library error.

## desktop entry setup (Linux)

run:
```bash
./setup.sh
```

## Default keyboard shortcuts

| Action              | Shortcut         |
|----------------------|------------------|
| Floating URL/search  | `Ctrl+Space`     |
| Launcher (Omarchy-style) | `Ctrl+K`     |
| Command palette       | `Ctrl+Shift+P`   |
| Switch tabs            | `Ctrl+Tab`       |
| New tab                | `Ctrl+T`         |
| Close tab               | `Ctrl+W`         |
| Bookmarks                | `Ctrl+B`         |
| History                   | `Ctrl+H`         |
| Downloads                  | `Ctrl+J`         |
| Settings                    | `Ctrl+,`         |
| Toggle dark mode              | `Ctrl+Alt+L`     |
| Fullscreen                   | `F11`            |
| Quit                          | `Ctrl+Q`         |

Every binding above is stored in `config/shortcuts.json` and can be
edited freely — no code changes required. The launcher's default is
`Ctrl+K` rather than the bare Super key, since most window managers
(including Hyprland/Omarchy) already reserve Super; rebind it to
whatever your compositor leaves free.

### Vim mode

Enabled by default (`vim_mode: true` in `config/settings.json`).
While a page has focus and you're not typing in a text field:

`j`/`k` scroll · `h`/`l` back/forward · `gg`/`G` top/bottom ·
`yy` copy URL · `p` open clipboard URL · `o` URL popup ·
`t` tab popup · `b` bookmarks · `r` reload

Rebind these under the `"vim"` key in `config/shortcuts.json`.

## Project layout

```
VoidBrowser/
├── main.py            entry point
├── browser.py         glue layer: wires managers, popups, shortcuts, vim mode
├── window.py           main window + void://home homepage generator
├── tabs.py              tab lifecycle (no visible tab bar; QStackedWidget-backed)
├── commands.py            shared command registry (launcher + command palette)
├── popup.py                base class for every floating popup
├── shortcuts.py             loads/binds config/shortcuts.json
├── themes.py                 loads themes/*.json, generates QSS
├── settings.py                config/settings.json manager
├── search.py                   config/search.json + URL/query resolution
├── history.py                   data/history.json manager
├── bookmarks.py                  data/bookmarks.json manager
├── downloads.py                   Qt WebEngine download tracking
├── workspace.py                    multi-workspace session persistence
├── plugin_loader.py                 auto-loads plugins/*.py
│
├── config/         settings.json, shortcuts.json, search.json, startup.json
├── themes/          omarchy.json, nord.json, gruvbox.json, catppuccin.json, void.json
├── data/             history.json, bookmarks.json, pinned.json, sessions.json, downloads.json
├── ui/                 command_palette.py, launcher.py, url_popup.py, tab_popup.py,
│                        bookmark_popup.py, history_popup.py, downloads_popup.py, settings_popup.py
└── plugins/              drop-in .py files auto-loaded at startup (see example_plugin.py)
```

## Customizing

- **Dark mode**: a real light theme (`themes/light.json`) ships alongside
  the five dark themes. Toggle it from Settings (`Ctrl+,`), the command
  palette (`Toggle Dark Mode`), or `Ctrl+Alt+L`. VoidBrowser remembers
  which dark theme you were using and restores it when you toggle back.
  A second setting, "Force dark mode on websites" (on by default), uses
  Chromium's built-in dark renderer so page content matches the browser
  chrome instead of staying whatever colors the site shipped with. This
  needs Qt 6.7+; on older PySide6 it's silently skipped.
- **Themes**: add a new JSON file to `themes/` with the same keys as
  `themes/void.json` (including a `"dark": true/false` flag), then select
  it from the Settings popup (`Ctrl+,`) or the command palette.
- **Shortcuts**: edit `config/shortcuts.json`. Any Qt key-sequence
  string works (e.g. `"Ctrl+Alt+T"`).
- **Search engines**: edit `config/search.json`; add an entry under
  `"engines"` with a `{query}` placeholder in `"url"`.
- **Plugins**: drop a `.py` file into `plugins/` with a `register(browser)`
  function. See `plugins/example_plugin.py`. Plugins get access to the
  full `Browser` instance — command registry, settings, shortcuts, tabs,
  and every popup — so they can add commands, launcher entries, or
  keybindings without touching core files.

## Known limitations / what's stubbed for now

This is a complete, runnable scaffold covering every module in the
spec, but a few pieces are intentionally minimal and are good next
places to extend:

- **Vim mode** covers the core navigation set (scroll, history, gg/G,
  yank/paste URL, popups) via a lightweight event filter — it does not
  yet implement link-hint mode (`f`) or in-page search (`/`, `n`, `N`).
- **Split view** and **workspace switching UI** are wired at the data
  layer (`workspace.py`) but don't yet have a dedicated popup — use the
  command palette's "Switch workspace" hook point to build one.
- **Website permissions manager** and **incognito profile isolation**
  are represented as a settings toggle; a fully isolated
  `QWebEngineProfile` for incognito tabs is a natural next step.

  
<img width="1773" height="867" alt="screenshot-2026-07-11_21-45-44" src="https://github.com/user-attachments/assets/b66bf470-5e95-4c24-a804-be824a57067c" />
<img width="1833" height="936" alt="screenshot-2026-07-11_21-44-54" src="https://github.com/user-attachments/assets/399ca439-0a19-48a6-bd07-6eb6e9214a75" />
<img width="604" height="781" alt="screenshot-2026-07-11_21-48-58" src="https://github.com/user-attachments/assets/abc932e0-0457-4fe0-b72d-1f23b460737f" />
