#!/usr/bin/env bash

# install.sh
#
# Installs VoidBrowser as a normal Linux application.
# It:
#   1. Installs the application icons
#   2. Creates a desktop launcher
#   3. Refreshes desktop/icon caches

set -e

# Directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Project root (install.sh is expected to be here)
APP_DIR="$SCRIPT_DIR"

DESKTOP_DIR="$HOME/.local/share/applications"
ICON_BASE="$HOME/.local/share/icons/hicolor"

echo "==> Installing VoidBrowser from:"
echo "    $APP_DIR"

echo
echo "==> Installing icons"

mkdir -p "$ICON_BASE/scalable/apps"

if [[ -f "$APP_DIR/icons/void-browser.svg" ]]; then
    cp "$APP_DIR/icons/void-browser.svg" \
       "$ICON_BASE/scalable/apps/voidbrowser.svg"
fi

for size in 16 32 48 64 128 256 512; do
    mkdir -p "$ICON_BASE/${size}x${size}/apps"

    if [[ -f "$APP_DIR/icons/void-browser-${size}.png" ]]; then
        cp "$APP_DIR/icons/void-browser-${size}.png" \
           "$ICON_BASE/${size}x${size}/apps/voidbrowser.png"
    fi
done

echo
echo "==> Creating desktop entry"

mkdir -p "$DESKTOP_DIR"

if [[ ! -f "$APP_DIR/packaging/voidbrowser.desktop" ]]; then
    echo "ERROR: packaging/voidbrowser.desktop not found!"
    exit 1
fi

sed "s|INSTALL_DIR|$APP_DIR|g" \
    "$APP_DIR/packaging/voidbrowser.desktop" \
    > "$DESKTOP_DIR/voidbrowser.desktop"

chmod 644 "$DESKTOP_DIR/voidbrowser.desktop"

echo
echo "==> Refreshing desktop database"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$DESKTOP_DIR"
fi

echo
echo "==> Refreshing icon cache"

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$ICON_BASE" || true
fi

echo
echo "========================================"
echo " VoidBrowser installed successfully!"
echo "========================================"
echo
echo "You should now find 'VoidBrowser' in:"
echo "  • GNOME"
echo "  • KDE Plasma"
echo "  • XFCE"
echo "  • Cinnamon"
echo "  • Rofi"
echo "  • Wofi"
echo "  • Fuzzel"
echo
echo "If it doesn't appear immediately, log out and back in,"
echo "or restart your launcher."
