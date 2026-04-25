#!/usr/bin/env python3
"""
wake.py — wake an Apple ADC CRT (or LCD Studio Display) on macOS.

Why this exists: the rest of this repo is Linux-only (acdcontrol.cpp uses
<linux/hiddev.h>). On macOS we talk to the same monitor via hidapi.

Setup, one time:
    brew install hidapi
    python3 -m pip install --user hid

Run:
    python3 wake.py

If the monitor still won't wake after this script reports success, the
problem is video sync (DAC / resolution), not USB control — software
can't fix that.
"""

import sys

try:
    import hid
except ImportError:
    sys.exit(
        "missing 'hid' module. install with:\n"
        "  brew install hidapi\n"
        "  python3 -m pip install --user hid"
    )

APPLE_VID = 0x05AC

# Known Apple display product IDs that respond to HID feature reports.
# 0x9213 is the M7768 17" ADC CRT (per mega-calibrator).
# 0x9217 is acdcontrol's "Studio Display 17" LCD.
# We try every Apple display we can open; harmless on the wrong one.
CANDIDATE_PIDS = [
    0x9213, 0x9215, 0x9217, 0x9218, 0x9219, 0x921B, 0x921C,
    0x921E, 0x9221, 0x9222, 0x9226, 0x9227, 0x9232, 0x9236,
]


def find_displays():
    found = []
    for info in hid.enumerate(APPLE_VID, 0):
        if info["product_id"] in CANDIDATE_PIDS:
            found.append(info)
    return found


def brightness_max(dev):
    """Brightness is the only command acdcontrol uses successfully
    (acdcontrol.cpp:461-481). Report ID 0x10, 16-bit little-endian value,
    range 0-750. Sending max should be visible if the monitor is awake."""
    dev.send_feature_report(bytes([0x10, 0xEE, 0x02]))


def brightness_read(dev):
    raw = dev.get_feature_report(0x10, 3)
    if len(raw) >= 3:
        return raw[1] | (raw[2] << 8)
    return None


def power_on(dev):
    """VCP D6, value 1 = on. Layout is a guess from mega-calibrator;
    if length is wrong hidapi raises rather than misbehaving."""
    dev.send_feature_report(bytes([0xD6, 0x01]))


def main():
    displays = find_displays()
    if not displays:
        print("no Apple display found on USB.")
        print("check `system_profiler SPUSBDataType | grep -A6 0x05ac`")
        print("if nothing shows there either, the adapter isn't passing")
        print("the ADC USB pair through — this is a hardware problem.")
        return 1

    for info in displays:
        pid = info["product_id"]
        path = info["path"]
        print(f"found Apple display VID=0x{APPLE_VID:04x} PID=0x{pid:04x}")
        try:
            dev = hid.Device(path=path)
        except Exception as e:
            print(f"  open failed: {e}")
            continue

        try:
            current = brightness_read(dev)
            print(f"  current brightness reads as: {current}")
        except Exception as e:
            print(f"  brightness read failed: {e}")

        for label, fn in [("brightness max", brightness_max),
                          ("power on", power_on)]:
            try:
                fn(dev)
                print(f"  {label}: sent")
            except Exception as e:
                print(f"  {label}: {e}")

        dev.close()

    print()
    print("if the screen is still dark, try forcing 1024x768 @ 75Hz")
    print("on the Mac (System Settings -> Displays -> option-click Scaled).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
