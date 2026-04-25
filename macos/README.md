# macOS quick-wake

Pull this branch on your Mac, then:

```
brew install hidapi
python3 -m pip install --user hid
python3 macos/wake.py
```

`wake.py` enumerates Apple displays over USB, sends a brightness-max
feature report (the only command we know is reliable), and tries a
power-on VCP command as a fallback.

If `wake.py` says "no Apple display found on USB", the adapter's USB pair
isn't passing through to the Mac — that's a hardware problem and no
software will fix it. Cross-check with:

```
system_profiler SPUSBDataType | grep -B2 -A8 0x05ac
```

If `wake.py` reports commands sent but the screen stays dark, the issue
is video sync, not HID — try forcing 1024x768 @ 75 Hz on the Mac via
System Settings → Displays → option-click "Scaled".
