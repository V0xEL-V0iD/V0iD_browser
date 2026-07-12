#!/usr/bin/env bash
# install.sh — makes VoidBrowser show up like a normal installed Linux app:
# a launcher entry (Rofi/Wofi/Fuzzel/GNOME/KDE menus, wherever) with a real
# icon, instead of something you have to `cd` into a folder and run.
#
# Usually you don't need to run this directly -- use setup.sh from the
# project root, which installs dependencies first and then calls this.
# Run it directly only if dependencies are already installed and you just
# want to (re)install the launcher entry + icon.
#
# What it does:
#   1. Copies the app icon into ~/.local/share/icons/hicolor/...
#   2. Generates ~/.local/share/applications/voidbrowser.desktop pointing
#      at THIS folder (wherever you've put it)
#   3. Refreshes the desktop/icon caches so the entry shows up immediately
#
# Run it from inside the VoidBrowser project folder:
#   chmod +x install.sh && ./install.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_BASE="$HOME/.local/share/icons/hicolor"

echo "==> Installing VoidBrowser desktop entry from: $APP_DIR"

echo "==> Installing icons"
mkdir -p "$ICON_BASE/scalable/apps"
cp "$APP_DIR/icons/void-browser.svg" "$ICON_BASE/scalable/apps/voidbrowser.svg"
for size in 16 32 48 64 128 256 512; do
    mkdir -p "$ICON_BASE/${size}x${size}/apps"
    cp "$APP_DIR/icons/void-browser-${size}.png" "$ICON_BASE/${size}x${size}/apps/voidbrowser.png"
done

echo "==> Writing desktop entry"
mkdir -p "$DESKTOP_DIR"
sed "s|__INSTALL_DIR__|$APP_DIR|g" "$APP_DIR/packaging/voidbrowser.desktop" \
    > "$DESKTOP_DIR/voidbrowser.desktop"
chmod +x "$DESKTOP_DIR/voidbrowser.desktop"

echo "==> Refreshing caches (best-effort)"
command -v update-desktop-database >/dev/null 2>&1 && \
    update-desktop-database "$DESKTOP_DIR" || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && \
    gtk-update-icon-cache -f -t "$ICON_BASE" || true

echo
echo "Done. VoidBrowser should now appear in your app launcher"
echo "(Rofi/Wofi/Fuzzel/GNOME/KDE menus) as a normal app."
echo "If it doesn't show up immediately, log out/in or restart your launcher."
