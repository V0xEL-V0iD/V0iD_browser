#!/usr/bin/env bash
# setup.sh — run this once after downloading VoidBrowser.
#
#   chmod +x setup.sh && ./setup.sh
#
# What it does:
#   1. Checks you have a suitable Python 3
#   2. Installs the Python dependencies (PySide6 / Qt WebEngine)
#   3. Optionally installs the app launcher entry + icon (packaging/install.sh)
#
# Safe to re-run any time -- it won't duplicate anything.

set -e

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$APP_DIR"

echo "=================================="
echo " VoidBrowser setup"
echo "=================================="
echo

# -- 1. Python version check --------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 was not found on your PATH. Install Python 3.11+ first, then re-run this script."
    exit 1
fi

PY_VERSION="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
PY_OK="$(python3 -c 'import sys; print(1 if sys.version_info >= (3, 11) else 0)')"

echo "==> Found Python $PY_VERSION"
if [ "$PY_OK" != "1" ]; then
    echo "    Warning: VoidBrowser expects Python 3.11+. Things may not work correctly."
fi

# -- 2. Install dependencies ---------------------------------------------
echo
echo "==> Installing dependencies from requirements.txt"
if pip install --user -r requirements.txt 2>/dev/null; then
    :
elif pip install --user --break-system-packages -r requirements.txt 2>/dev/null; then
    :
else
    echo "    pip install failed. If you're on a distro that blocks system-wide pip installs,"
    echo "    try creating a virtual environment first:"
    echo "        python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi
echo "    Dependencies installed."

# -- 3. Optional desktop integration --------------------------------------
echo
read -r -p "Install VoidBrowser as an app in your launcher menu too? [Y/n] " REPLY
REPLY="${REPLY:-Y}"
if [[ "$REPLY" =~ ^[Yy] ]]; then
    if [ -x "$APP_DIR/packaging/install.sh" ]; then
        "$APP_DIR/packaging/install.sh"
    else
        bash "$APP_DIR/packaging/install.sh"
    fi
else
    echo "    Skipped. You can run packaging/install.sh yourself later if you change your mind."
fi

echo
echo "=================================="
echo " Setup complete"
echo "=================================="
echo "Run VoidBrowser with:"
echo "    python3 $APP_DIR/main.py"
echo "or from your app launcher, if you installed the desktop entry above."
