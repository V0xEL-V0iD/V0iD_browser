#!/usr/bin/env bash
# uninstall.sh — removes the desktop entry and icons installed by install.sh.
# Does NOT touch the project folder itself, your config, or your browsing data.

set -e

DESKTOP_DIR="$HOME/.local/share/applications"
ICON_BASE="$HOME/.local/share/icons/hicolor"

echo "==> Removing desktop entry"
rm -f "$DESKTOP_DIR/voidbrowser.desktop"

echo "==> Removing icons"
rm -f "$ICON_BASE/scalable/apps/voidbrowser.svg"
for size in 16 32 48 64 128 256 512; do
    rm -f "$ICON_BASE/${size}x${size}/apps/voidbrowser.png"
done

command -v update-desktop-database >/dev/null 2>&1 && \
    update-desktop-database "$DESKTOP_DIR" || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && \
    gtk-update-icon-cache -f -t "$ICON_BASE" || true

echo "Done. VoidBrowser removed from your app launcher."
echo "The project folder itself is untouched -- delete it manually if you want."
