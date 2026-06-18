#!/bin/bash

# Script to remove the Dell G15 AlienFx application menu shortcut

DESKTOP_FILE="$HOME/.local/share/applications/dell-g15-alienfx.desktop"

echo "Removing App Menu shortcut..."

if [ -f "$DESKTOP_FILE" ]; then
    rm "$DESKTOP_FILE"
    echo "Successfully removed 'Dell G15 AlienFx' from the application menu."
else
    echo "Menu shortcut not found. Nothing to remove."
fi
