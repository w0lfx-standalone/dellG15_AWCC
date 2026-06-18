#!/usr/bin/env python3
# Dell G15 Controller - Main UI

import sys
import pexpect
import tempfile
import awelc
import PySide6
from PySide6.QtCore import (QSettings, QTimer)
from PySide6.QtGui import (QIcon, QAction)
from PySide6.QtWidgets import (QColorDialog, QMessageBox, QGridLayout, QGroupBox, QWidget, QPushButton, QApplication,
                               QVBoxLayout, QHBoxLayout, QDialog, QSlider, QLabel, QMenu, QComboBox, QTabWidget)
from patch import g15_5530_patch, g15_5520_patch, g15_5515_patch, g15_5511_patch, g16_7630_patch

class MainWindow(QWidget):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.is_dell_g_series = False
        self.is_keyboard_supported = True 
        self.model = 'Unknown'
        
        try:
            self.logfile = open("/tmp/dell-g-series-controller.log", "w")
            sys.stdout = self.logfile
        except:
            print("Failed to open log file")
            exit()
        
        self.init_acpi_call()
        self.setMinimumWidth(600)
        self.setWindowTitle("Dell G Series Controller")
        self.settings = QSettings('Dell-G15', 'Controller')
        
        # Load zone colors
        self.zone_colors = []
        default_colors = ["#ff0000", "#00ff00", "#0000ff", "#ffff00"]
        for i in range(4):
            hex_color = self.settings.value(f"Zone_{i}_Color", default_colors[i])
            self.zone_colors.append(PySide6.QtGui.QColor(hex_color))

        try:
            self.brightness_level = int(self.settings.value("Brightness", 0))
        except:
            self.brightness_level = 0

        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tabs.addTab(self.tab1, "Lighting")
        self.tabs.addTab(self.tab2, "Cooling")

        # Lighting UI
        layout1 = QVBoxLayout()
        layout1.addWidget(QLabel(f'Model: Dell {self.model}' if self.model != 'Unknown' else f'Model: {self.model}'))
        layout1.addWidget(self._create_lighting_group())
        self.tab1.setLayout(layout1)

        self.combobox_choice()

        # Cooling UI
        layout2 = QVBoxLayout()
        self.timer = None
        if (self.is_root and self.is_dell_g_series):
            layout2.addWidget(self._create_cooling_group())
            self.timer = QTimer(self)
            self.timer.setInterval(1000)
            self.timer.timeout.connect(self.get_rpm_and_temp)
            self.timer.start()
        else:
            layout2.addWidget(QLabel("Root access and supported hardware required for fans/power."))
        self.tab2.setLayout(layout2)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def closeEvent(self, event):
        if hasattr(self, 'timer') and self.timer:
            self.timer.stop()
        if hasattr(self, 'logfile') and self.logfile:
            self.logfile.close()
        event.accept()

    def init_acpi_call(self):
        self.power_modes_dict = {
            "USTT_Balanced" : "0xa0",
            "USTT_Performance" : "0xa1",
            "USTT_Quiet" : "0xa3",
            "USTT_FullSpeed": "0xa4",
            "USTT_BatterySaver" : "0xa5",
            "G Mode" : "0xab",
            "Manual" : "0x0",
        }
            
        self.acpi_call_dict = {
            "get_laptop_model" : ["0x1a", "0x02", "0x02"],
            "get_power_mode" : ["0x14", "0x0b", "0x00"],
            "set_power_mode" : ["0x15", "0x01"],
            "toggle_G_mode" : ["0x25", "0x01"],
            "get_G_mode" : ["0x25", "0x02"],
            "set_fan1_boost" : ["0x15", "0x02", "0x32"],
            "get_fan1_boost" : ["0x14", "0x0c", "0x32"],
            "get_fan1_rpm" : ["0x14", "0x05", "0x32"],
            "get_cpu_temp" : ["0x14", "0x04", "0x01"],
            "set_fan2_boost" : ["0x15", "0x02", "0x33"],
            "get_fan2_boost" : ["0x14", "0x0c", "0x33"],
            "get_fan2_rpm" : ["0x14", "0x05", "0x33"],
            "get_gpu_temp" : ["0x14", "0x04", "0x06"]
        }
        
        print("Opening elevated bash shell...")
        self.shell = pexpect.spawn('bash', encoding='utf-8', logfile=self.logfile, env=None, args=["--noprofile", "--norc"])
        self.shell.expect("[#$] ")
        self.shell_exec(" export HISTFILE=/dev/null; history -c")
        
        self.shell_exec("pkexec bash --noprofile --norc")
        self.shell_exec(" export HISTFILE=/dev/null; history -c")
        
        self.is_root = (self.shell_exec("whoami")[1].find("root") != -1)
        if not self.is_root:
            print("No root access. ACPI disabled.")
            popup = QMessageBox.warning(self, "Warning", "No root access. Power/Fan functions disabled.")
            return

        self.shell_exec("modprobe acpi_call")
        self._check_laptop_model()

        if not self.is_dell_g_series:
            choice = QMessageBox.question(self, "Unrecognized laptop", "Model not officially supported. Try anyway? (Risk of hardware damage)", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            self.is_dell_g_series = (choice == QMessageBox.StandardButton.Yes)
    
    def _check_laptop_model(self):
        # Intel models
        self.acpi_cmd = "echo \"\\_SB.AMWW.WMAX 0 {} {{{}, {}, {}, 0x00}}\" | tee /proc/acpi/call; cat /proc/acpi/call"
        laptop_model = self.acpi_call("get_laptop_model")
        
        if (laptop_model == "0x0"):
            self.is_dell_g_series = True
            self.model = "G15 5530 / G16 7630"
            g15_5530_patch(self)
            return

        if (laptop_model == "0x12c0"):
            self.is_dell_g_series = True
            self.model = "G15 5520"
            g15_5520_patch(self)
            return

        if (laptop_model == "0xc80"):
            self.is_dell_g_series = True
            self.model = "G15 5511"
            g15_5511_patch(self)
            return

        # AMD models
        self.acpi_cmd = "echo \"\\_SB.AMW3.WMAX 0 {} {{{}, {}, {}, 0x00}}\" | tee /proc/acpi/call; cat /proc/acpi/call"
        laptop_model = self.acpi_call("get_laptop_model")

        if (laptop_model == "0x12c0"):
            self.is_dell_g_series = True
            self.model = "G15 5525"
            return

        if (laptop_model == "0xc80"):
            self.is_dell_g_series = True
            self.model = "G15 5515"
            g15_5515_patch(self)

    def _create_lighting_group(self):
        groupBox = QGroupBox("Keyboard RGB (4 Zones)")
        vbox = QVBoxLayout()
        if self.is_keyboard_supported:
            grid_zones = QGridLayout()
            self.zone_buttons = []
            self.zone_labels = []
            zone_names = ["Zone 1 (Left)", "Zone 2 (Middle)", "Zone 3 (Right)", "Zone 4 (Numpad)"]
            
            for i in range(4):
                label = QLabel(zone_names[i])
                btn = QPushButton()
                btn.setMinimumHeight(30)
                self.update_button_color(btn, self.zone_colors[i])
                btn.clicked.connect(lambda checked=False, idx=i: self.pick_zone_color(idx))
                self.zone_buttons.append(btn)
                self.zone_labels.append(label)
                grid_zones.addWidget(label, i, 0)
                grid_zones.addWidget(btn, i, 1)
            
            vbox.addLayout(grid_zones)

            # Brightness slider
            hbox_bright = QHBoxLayout()
            hbox_bright.addWidget(QLabel("Brightness:"))
            self.slider_brightness = QSlider(PySide6.QtCore.Qt.Orientation.Horizontal)
            self.slider_brightness.setMinimum(0)
            self.slider_brightness.setMaximum(2)
            self.slider_brightness.setTickPosition(QSlider.TickPosition.TicksBelow)
            self.slider_brightness.setTickInterval(1)
            self.slider_brightness.setFixedWidth(150)
            
            rev_map = {100: 0, 50: 1, 0: 2}
            self.slider_brightness.setValue(rev_map.get(self.brightness_level, 2))
            self.slider_brightness.valueChanged.connect(self.change_brightness)

            hbox_bright.addWidget(self.slider_brightness)
            hbox_bright.addWidget(QLabel(" (Off — Med — Full)"))
            hbox_bright.addStretch()
            vbox.addLayout(hbox_bright)

            self.duration_label = QLabel("Duration")
            self.duration = QSlider(orientation=PySide6.QtCore.Qt.Orientation.Horizontal)
            self.duration.setMinimum(4)
            self.duration.setMaximum(4095)
            self.duration.setValue(int(self.settings.value("Duration", 255)))

            self.tempo_label = QLabel("Speed")
            self.tempo = QSlider(orientation=PySide6.QtCore.Qt.Orientation.Horizontal)
            self.tempo.setMinimum(1)
            self.tempo.setMaximum(255)
            self.tempo.setValue(int(self.settings.value("Tempo", 1)))

            mode_widget = QWidget()
            hbox_mode = QHBoxLayout(mode_widget)
            self.combobox_mode = QComboBox()
            self.combobox_mode.addItems(["Static (4 Zones)", "Single Color Pulse", "Rainbow Cycle", "Off"])
            self.combobox_mode.setCurrentText(self.settings.value("Action", "Static (4 Zones)"))
            self.combobox_mode.currentTextChanged.connect(self.combobox_choice)

            self.button_apply = QPushButton("Apply")
            self.button_apply.clicked.connect(self.apply_leds)
            self.button_restore = QPushButton("Restore Slot 0x61")
            self.button_restore.clicked.connect(self.restore_preset)

            hbox_mode.addWidget(self.combobox_mode)
            hbox_mode.addWidget(self.button_apply)

            vbox.addWidget(self.duration_label)
            vbox.addWidget(self.duration)
            vbox.addWidget(self.tempo_label)
            vbox.addWidget(self.tempo)
            vbox.addWidget(mode_widget)
            vbox.addWidget(self.button_restore)
        else:
            vbox.addWidget(QLabel("Keyboard RGB not supported on this model."))
            
        groupBox.setLayout(vbox)
        return groupBox

    def _create_cooling_group(self):
        groupBox = QGroupBox("Fans and Power")
        vbox = QVBoxLayout()

        self.combobox_mode_power = QComboBox()
        self.combobox_mode_power.addItems(self.power_modes_dict.keys())
        self.combobox_mode_power.setCurrentText(self.settings.value("Power", "USTT_Balanced"))
        self.combobox_mode_power.currentTextChanged.connect(self.combobox_power)

        self.info_label = QLabel("")
        self.info_label.setWordWrap(True)

        # CPU Fan
        vbox.addWidget(QLabel("CPU Fan Boost"))
        hbox1 = QHBoxLayout()
        self.fan1_boost = QSlider(orientation=PySide6.QtCore.Qt.Orientation.Horizontal)
        self.fan1_boost.setRange(0, 255)
        self.fan1_boost.setValue(int(self.settings.value("Fan1 Boost", 0)))
        self.fan1_boost.sliderReleased.connect(self.slider_fan1)
        self.fan1_current = QLabel("0 RPM")
        hbox1.addWidget(self.fan1_boost)
        hbox1.addWidget(self.fan1_current)
        vbox.addLayout(hbox1)

        # GPU Fan
        vbox.addWidget(QLabel("GPU Fan Boost"))
        hbox2 = QHBoxLayout()
        self.fan2_boost = QSlider(orientation=PySide6.QtCore.Qt.Orientation.Horizontal)
        self.fan2_boost.setRange(0, 255)
        self.fan2_boost.setValue(int(self.settings.value("Fan2 Boost", 0)))
        self.fan2_boost.sliderReleased.connect(self.slider_fan2)
        self.fan2_current = QLabel("0 RPM")
        hbox2.addWidget(self.fan2_boost)
        hbox2.addWidget(self.fan2_current)
        vbox.addLayout(hbox2)

        vbox.addWidget(self.combobox_mode_power)
        vbox.addWidget(self.info_label)
        
        groupBox.setLayout(vbox)
        return groupBox

    def update_button_color(self, btn, color):
        btn.setStyleSheet(f"background-color: {color.name()}; border: 1px solid gray;")

    def pick_zone_color(self, idx):
        color = QColorDialog.getColor(self.zone_colors[idx], self, "Select Color")
        if color.isValid():
            self.zone_colors[idx] = color
            self.update_button_color(self.zone_buttons[idx], color)
            self.settings.setValue(f"Zone_{idx}_Color", color.name())

    def change_brightness(self, value):
        levels = {0: 100, 1: 50, 2: 0}
        self.brightness_level = levels[value]
        self.settings.setValue("Brightness", self.brightness_level)
        awelc.set_dim(self.brightness_level)

    def combobox_choice(self):
        mode = self.combobox_mode.currentText()
        self.settings.setValue("Action", mode)
        
        # Hide/Show controls based on mode
        is_static = (mode == "Static (4 Zones)")
        is_pulse = (mode == "Single Color Pulse")
        is_rainbow = (mode == "Rainbow Cycle")
        
        for i in range(4):
            show = is_static or (is_pulse and i == 0)
            self.zone_labels[i].setVisible(show)
            self.zone_buttons[i].setVisible(show)
        
        self.zone_labels[0].setText("Pulse Color" if is_pulse else "Zone 1 (Left)")
        self.duration_label.setVisible(is_pulse or is_rainbow)
        self.duration.setVisible(is_pulse or is_rainbow)
        self.tempo_label.setVisible(is_pulse or is_rainbow)
        self.tempo.setVisible(is_pulse or is_rainbow)

    def apply_leds(self):
        try:
            mode = self.combobox_mode.currentText()
            self.settings.setValue("Duration", self.duration.value())
            self.settings.setValue("Tempo", self.tempo.value())

            if mode == "Static (4 Zones)":
                colors = [(c.red(), c.green(), c.blue()) for c in self.zone_colors]
                awelc.set_4zone_static(colors)
            elif mode == "Single Color Pulse":
                c = self.zone_colors[0]
                awelc.set_single_color_morph(c.red(), c.green(), c.blue(), self.duration.value(), self.tempo.value())
            elif mode == "Rainbow Cycle":
                awelc.set_rainbow_morph(self.duration.value(), self.tempo.value())
            else:
                awelc.remove_animation()

            awelc.set_dim(self.brightness_level)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to apply RGB: {e}")

    def restore_preset(self):
        try:
            elc, device = awelc.init_device()
            elc.play_animation(0x61)
            device.reset()
            QMessageBox.information(self, "Success", "Restored preset 0x61")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed: {e}")

    def combobox_power(self):
        self.fan1_boost.setValue(0)
        self.fan2_boost.setValue(0)
        choice = self.combobox_mode_power.currentText()
        self.settings.setValue("Power", choice)
        
        mode_hex = self.power_modes_dict[choice]
        self.acpi_call("set_power_mode", mode_hex)
        
        # Confirmation check
        confirmed = self.acpi_call("get_power_mode")
        msg = f"Mode set to {choice}." if confirmed == mode_hex else f"Error setting mode! (Got {confirmed})"
        
        # Handle G-Mode toggle
        is_gmode = (choice == "G Mode")
        current_g = self.acpi_call("get_G_mode")
        if is_gmode != (current_g == "0x1"):
            self.acpi_call("toggle_G_mode")
            
        self.info_label.setText(msg)

    def slider_fan1(self):
        val = self.fan1_boost.value()
        self.acpi_call("set_fan1_boost", "0x{:2X}".format(val))
        self.settings.setValue("Fan1 Boost", val)

    def slider_fan2(self):
        val = self.fan2_boost.value()
        self.acpi_call("set_fan2_boost", "0x{:2X}".format(val))
        self.settings.setValue("Fan2 Boost", val)

    def get_rpm_and_temp(self):
        if self.isVisible():
            f1 = self.acpi_call("get_fan1_rpm")
            t1 = self.acpi_call("get_cpu_temp")
            f2 = self.acpi_call("get_fan2_rpm")
            t2 = self.acpi_call("get_gpu_temp")
            self.fan1_current.setText(f"{int(f1,0)} RPM, {int(t1,0)} °C")
            self.fan2_current.setText(f"{int(f2,0)} RPM, {int(t2,0)} °C")

    def acpi_call(self, cmd, arg1="0x00", arg2="0x00"):
        args = self.acpi_call_dict[cmd]
        if len(args) == 4:
            cmd_str = self.acpi_cmd.format(args[0], args[1], args[2], args[3])
        elif len(args) == 3:
            cmd_str = self.acpi_cmd.format(args[0], args[1], args[2], arg1)
        elif len(args) == 2:
            cmd_str = self.acpi_cmd.format(args[0], args[1], arg1, arg2)
        else:
            return "0x0"
        return self.parse_shell_exec(self.shell_exec(cmd_str)[2])

    def shell_exec(self, cmd):
        self.shell.sendline(cmd)
        self.shell.expect("[#$] ")
        return self.shell.before.split('\n')

    def parse_shell_exec(self, line):
        return line[line.find('\r')+1:line.find('\x00')]

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
