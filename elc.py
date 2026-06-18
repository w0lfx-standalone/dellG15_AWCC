#!/usr/bin/python3
# Low-level HID communication with the LED controller

import usb
import sys
import struct
from elc_constants import *
from hidreport import *
import binascii

class Action:
    def __init__(self, effect, duration, tempo, red, green, blue):
        self.effect = effect
        self.duration = duration
        self.tempo = tempo
        self.red = red
        self.green = green
        self.blue = blue

    def __str__(self):
        fragment = format(self.effect, '02x')
        fragment += format(self.duration, '04x')
        fragment += format(self.tempo, '04x')
        fragment += format(self.red, '02x')
        fragment += format(self.green, '02x')
        fragment += format(self.blue, '02x')
        return fragment

class Elc:
    def build_command(self, fragment):
        bytes = bytearray.fromhex(fragment)
        bytes += bytearray.fromhex('00' * (33 - len(bytes)))
        return bytes

    def run_command(self, device, fragment):
        bytes = self.build_command('03' + fragment)
        hid_set_output_report(device, bytes)
        return bytearray(hid_get_input_report(device, 33))

    def get_version(self):
        reply = self.run_command(self.device, format(ELC_QUERY, '02x') + format(GET_VERSION, '02x'))
        return (reply[3], reply[4], reply[5])

    def get_animation_count(self):
        reply = self.run_command(self.device, format(ELC_QUERY, '02x') + format(GET_ANIMATION_COUNT, '02x'))
        return (struct.unpack('>H', reply[3:5])[0], struct.unpack('>H', reply[5:7])[0])

    def start_new_animation(self, animation):
        command = POWER_ANIMATION if (0x5b <= animation <= 0x60) else USER_ANIMATION
        return self.run_command(self.device, format(command, '02x') + format(START_NEW, '04x') + format(animation, "04x"))

    def finish_save_animation(self, animation):
        command = POWER_ANIMATION if (0x5b <= animation <= 0x60) else USER_ANIMATION
        return self.run_command(self.device, format(command, '02x') + format(FINISH_SAVE, '04x') + format(animation, "04x"))

    def remove_animation(self, animation):
        command = POWER_ANIMATION if (0x5b <= animation <= 0x60) else USER_ANIMATION
        return self.run_command(self.device, format(command, '02x') + format(REMOVE, '04x') + format(animation, "04x"))

    def set_default_animation(self, animation):
        command = POWER_ANIMATION if (0x5b <= animation <= 0x60) else USER_ANIMATION
        return self.run_command(self.device, format(command, '02x') + format(SET_DEFAULT, '04x') + format(animation, "04x"))

    def start_series(self, zones, loop=1):
        zonestring = "".join(format(x, "02x") for x in zones)
        return self.run_command(self.device, format(START_SERIES, '02x') + format(loop, "02x") + format(len(zones), "04x") + zonestring)

    def add_action(self, actions):
        fragment = format(ADD_ACTION, '02x')
        if len(actions) > 3:
            raise Exception("Too many actions")
        for k in actions:
            fragment += str(k)
        return self.run_command(self.device, fragment)

    def dim(self, zones, dimming):
        zonestring = "".join(format(x, '02x') for x in zones)
        fragment = format(DIMMING, '02x') + format(dimming, '02x') + format(len(zones), '04x') + zonestring
        return self.run_command(self.device, fragment)

    def __init__(self, vid, pid, debug=0):
        self.device = usb.core.find(idVendor=vid, idProduct=pid)
        self.debug = debug
