# Dell G15 AlienFx Controller

Quick tool to manage RGB, fans, and power modes on Dell G-Series laptops under Linux. Tested on G15 5530 but works for most 55xx/76xx models.

## What it does
- **RGB Control**: 4-zone support (Left, Middle, Right, Numpad) with Static, Rainbow, and Pulse modes.
- **Fans**: Real-time RPM/Temp monitoring + manual boost sliders.
- **Power**: Quick toggle for G-Mode and system power profiles (Performance, Quiet, etc).
- **Settings**: Remembers your colors and brightness between restarts.

## Installation

Just run the setup script:
```bash
sudo ./setup.sh
```
It handles the virtual environment, udev rules, and adds a shortcut to your app menu.
if any requirements fails, use the requirements.txt

To still add a app menu shortcut, run
```
./install_menu.sh
```
and to remove from menu,
```
./uninstall_menu.sh
```

## Requirements
- `acpi_call` module (for fans/power)
- `pkexec` (for root access to ACPI)
- `libusb` (for RGB)

## License
GPLv3
