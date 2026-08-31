"""Match Tk widget scale to the display without Windows-only Win32 calls.

HoloPatcher 1.5.1 asked shcore.SetProcessDpiAwareness through ctypes at
import time in the RTE editor. That API exists only on Windows, so opening
info.rte on Linux raised AttributeError and blocked the GUI. Tk already
knows the display DPI on every platform; ask it instead.
"""

from __future__ import annotations

from typing import Any


def apply_display_scaling(root: Any) -> None:
    """Set Tk's scaling from the display's pixels-per-inch."""
    try:
        pixels_per_inch = float(root.winfo_fpixels("1i"))
    except Exception:
        return
    if pixels_per_inch <= 0:
        return
    try:
        root.tk.call("tk", "scaling", pixels_per_inch / 72.0)
    except Exception:
        return
