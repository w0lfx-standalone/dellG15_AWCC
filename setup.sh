#!/bin/bash

# Dell G Series Controller - Robust Setup & Run Script
# This script installs dependencies, sets up udev rules, installs the F5 listener service, and runs the app.

set -e

BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$BASE_DIR/venv"

echo "--- Dell G Series Controller Perfection Setup ---"

# 1. Check & Install System Dependencies
echo "Checking system dependencies..."
MISSING_PKGS=()
if ! command -v python3 &>/dev/null; then MISSING_PKGS+=("python3"); fi
if ! dpkg -s python3-venv &>/dev/null; then MISSING_PKGS+=("python3-venv"); fi
if ! dpkg -s libusb-1.0-0 &>/dev/null; then MISSING_PKGS+=("libusb-1.0-0"); fi
if ! dpkg -s libxcb-cursor0 &>/dev/null; then MISSING_PKGS+=("libxcb-cursor0"); fi
if ! dpkg -s acpi-call-dkms &>/dev/null; then MISSING_PKGS+=("acpi-call-dkms"); fi

if [ ${#MISSING_PKGS[@]} -gt 0 ]; then
    echo "Installing missing system packages: ${MISSING_PKGS[*]} (requires sudo)..."
    sudo apt-get update -qq
    sudo apt-get install -y -qq "${MISSING_PKGS[@]}"
fi

# 2. Create/Update Virtual Environment
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

echo "Verifying Python dependencies..."
"$VENV_DIR/bin/pip" install --quiet PySide6 pyusb pexpect

# 3. Setup Udev Rules
echo "Setting up USB permissions (udev rules)..."
# Rule 1: 00-aw-elc.rules (for awelc symlink and 0550/0551 support)
if [ ! -f "/etc/udev/rules.d/00-aw-elc.rules" ]; then
    sudo cp "$BASE_DIR/00-aw-elc.rules" /etc/udev/rules.d/
fi

# Rule 2: 61-openrgb-dell.rules (for uaccess tags)
if [ ! -f "/etc/udev/rules.d/61-openrgb-dell.rules" ]; then
    echo 'SUBSYSTEMS=="usb|hidraw", ATTRS{idVendor}=="187c", ATTRS{idProduct}=="0551", TAG+="uaccess", TAG+="Dell_G_Series_LED_Controller"' | sudo tee /etc/udev/rules.d/61-openrgb-dell.rules > /dev/null
fi

sudo udevadm control --reload-rules && sudo udevadm trigger
echo "Udev rules updated."

# 4. Load ACPI module
if ! lsmod | grep -q "acpi_call"; then
    echo "Loading acpi_call module..."
    sudo modprobe acpi_call || echo "Warning: acpi_call module failed to load. Fan control might not work."
fi
sudo chmod 666 /proc/acpi/call 2>/dev/null || true

# 6. Create Desktop Shortcut
./install_menu.sh

echo "--- Setup Complete ---"
echo "Launching application..."

# Launch the app without hardcoded DISPLAY if possible
"$VENV_DIR/bin/python" "$BASE_DIR/main.py"
