#!/bin/bash

# Script to install the Dell G15 AlienFx application menu shortcut

BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_PYTHON="$BASE_DIR/venv/bin/python"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_PATH="$BASE_DIR/window.png"
DESKTOP_FILE="$DESKTOP_DIR/dell-g15-alienfx.desktop"

echo "Installing App Menu shortcut for 'Dell G15 AlienFx'..."

if [ ! -f "$VENV_PYTHON" ]; then
    echo "Error: Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

mkdir -p "$DESKTOP_DIR"

cat <<EOF > "$DESKTOP_FILE"
[Desktop Entry]
Encoding=UTF-8
Version=1.0
Type=Application
Terminal=false
Exec=$VENV_PYTHON $BASE_DIR/main.py
Path=$BASE_DIR
Name=Dell G15 AlienFx
Icon=$ICON_PATH
Categories=System;Settings;
Comment=Control RGB Lighting, Power Modes, and Fans for Dell G-Series/Alienware Laptops
EOF

chmod +x "$DESKTOP_FILE"

echo "Successfully installed! You can now find 'Dell G15 AlienFx' in your application menu."
