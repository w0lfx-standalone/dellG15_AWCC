#!/usr/bin/python3
# High-level RGB controls

import sys
import argparse
import random
from elc import *
from elc_constants import *

DURATION_MAX = 0xffff
DURATION_BATTERY_LOW = 0xff
DURATION_MIN = 0x00
TEMPO_MAX = 0xff
TEMPO_MIN = 0x01
ZONES = [0, 1, 2, 3]
ZONES_KB = [0, 1, 2]
ZONES_NP = [3]

def init_device():
    # 0550/0551 are the standard Dell/Alienware controller IDs
    supportedProducts = [0x0550, 0x0551]
    vid = 0x187C

    device = None
    for pid in supportedProducts:
        device = usb.core.find(idVendor=vid, idProduct=pid)
        if device:
            break

    if not device:
        raise Exception('No RGB controller found. (187c:0550 or 0551)')

    ep = device[0].interfaces()[0].endpoints()[0]
    i = device[0].interfaces()[0].bInterfaceNumber

    # Force detach if kernel is using it
    if device.is_kernel_driver_active(i):
        try:
            device.detach_kernel_driver(i)
        except usb.core.USBError as e:
            print(f"Driver detach failed: {e}")

    return Elc(vid, device.idProduct, debug=0), device

def apply_action(elc, red, green, blue, duration, tempo, animation=AC_CHARGING, effect=COLOR, zones=ZONES):
    if (effect == COLOR):
        elc.remove_animation(animation)
        elc.start_new_animation(animation)
        elc.start_series(zones)
        elc.add_action((Action(effect, duration, tempo, red, green, blue),))
        elc.finish_save_animation(animation)
        elc.set_default_animation(animation)
    else:  # Morph effect
        elc.remove_animation(animation)
        elc.start_new_animation(animation)
        elc.start_series(zones)
        elc.add_action((Action(MORPH, duration, tempo, red, green, blue), Action(MORPH, duration, tempo, green,
                       blue, red), Action(MORPH, duration, tempo, blue, red, green)))
        elc.finish_save_animation(animation)
        elc.set_default_animation(animation)

def battery_flashing(elc):
    # Flash red when battery is low
    elc.remove_animation(DC_LOW)
    elc.start_new_animation(DC_LOW)
    elc.start_series(ZONES)
    elc.add_action((Action(COLOR, DURATION_BATTERY_LOW, TEMPO_MIN, 255, 0, 0),))
    elc.add_action((Action(COLOR, DURATION_BATTERY_LOW, TEMPO_MIN, 0, 0, 0),))
    elc.finish_save_animation(DC_LOW)
    elc.set_default_animation(DC_LOW)

def set_static(red, green, blue):
    elc, device = init_device()
    elc.dim(ZONES, 0)
    apply_action(elc, 0, 0, 0, DURATION_MAX, TEMPO_MIN, AC_SLEEP, COLOR)
    apply_action(elc, red, green, blue, DURATION_MAX, TEMPO_MIN, AC_CHARGED, COLOR)
    apply_action(elc, red, green, blue, DURATION_MAX, TEMPO_MIN, AC_CHARGING, COLOR)
    apply_action(elc, 0, 0, 0, DURATION_MAX, TEMPO_MIN, DC_SLEEP, COLOR)
    apply_action(elc, int(red/2), int(green/2), int(blue/2), DURATION_MAX, TEMPO_MIN, DC_ON, COLOR)
    battery_flashing(elc)
    device.reset()

def set_4zone_static(colors):
    """ colors: list of 4 (r, g, b) tuples """
    elc, device = init_device()
    states = [AC_CHARGING, AC_CHARGED, DC_ON]
    
    for state in states:
        elc.remove_animation(state)
        elc.start_new_animation(state)
        for zone_id in range(4):
            r, g, b = colors[zone_id]
            elc.start_series([zone_id])
            elc.add_action((Action(COLOR, DURATION_MAX, TEMPO_MIN, r, g, b),))
        elc.finish_save_animation(state)
        elc.set_default_animation(state)
    
    battery_flashing(elc)
    device.reset()

def set_rainbow_morph(duration, tempo=0x01):
    elc, device = init_device()
    states = [AC_CHARGING, AC_CHARGED, DC_ON]
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)] # R, G, B
    
    for state in states:
        elc.remove_animation(state)
        elc.start_new_animation(state)
        # Shift colors across zones for a wave effect
        offsets = [0, 1, 2, 0] 
        for zone_id in range(4):
            elc.start_series([zone_id])
            idx = offsets[zone_id]
            z_colors = colors[idx:] + colors[:idx]
            elc.add_action((
                Action(MORPH, duration, tempo, z_colors[0][0], z_colors[0][1], z_colors[0][2]),
                Action(MORPH, duration, tempo, z_colors[1][0], z_colors[1][1], z_colors[1][2]),
                Action(MORPH, duration, tempo, z_colors[2][0], z_colors[2][1], z_colors[2][2])
            ))
        elc.finish_save_animation(state)
        elc.set_default_animation(state)
    
    battery_flashing(elc)
    device.reset()

def set_single_color_morph(r, g, b, duration, tempo=0x01):
    elc, device = init_device()
    states = [AC_CHARGING, AC_CHARGED, DC_ON]
    for state in states:
        elc.remove_animation(state)
        elc.start_new_animation(state)
        elc.start_series(ZONES)
        # Fade from color to black (pulse)
        elc.add_action((
            Action(MORPH, duration, tempo, r, g, b),
            Action(MORPH, duration, tempo, 0, 0, 0)
        ))
        elc.finish_save_animation(state)
        elc.set_default_animation(state)
    
    battery_flashing(elc)
    device.reset()

def remove_animation():
    set_dim(100)
    elc, device = init_device()
    for anim in [AC_SLEEP, AC_CHARGED, AC_CHARGING, DC_SLEEP, DC_ON, DC_LOW]:
        elc.remove_animation(anim)
    
    # Wipe any leftover animations
    animations = elc.get_animation_count()
    while animations != (0,0):
        elc.remove_animation(animations[1])
        animations = elc.get_animation_count()
    device.reset()

def set_dim(level):
    elc, device = init_device()
    elc.dim(ZONES, level)
    device.reset()
