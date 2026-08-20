# -*- coding: utf-8 -*-
"""Windows-specific window tweaks. Every function is a no-op on other platforms."""

from __future__ import annotations

import ctypes
import sys


def hide_from_taskbar(widget) -> None:
    """Remove the window from the taskbar by setting WS_EX_TOOLWINDOW.

    We deliberately do NOT use ``Qt.Tool`` — on Windows a parentless tool window
    stays hidden while the app is not focused. Instead the normal
    ``FramelessWindowHint | Window`` flags are used and the extended style is
    flipped directly, which hides the taskbar entry without hiding the window.
    """
    if sys.platform != "win32":
        return
    try:
        GWL_EXSTYLE = -20
        WS_EX_TOOLWINDOW = 0x00000080
        WS_EX_APPWINDOW = 0x00040000
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        SWP_NOZORDER = 0x0004
        SWP_FRAMECHANGED = 0x0020
        SWP_NOACTIVATE = 0x0010

        user32 = ctypes.windll.user32
        hwnd = int(widget.winId())
        getter = getattr(user32, "GetWindowLongPtrW", None) or user32.GetWindowLongW
        setter = getattr(user32, "SetWindowLongPtrW", None) or user32.SetWindowLongW
        getter.restype = ctypes.c_ssize_t
        setter.restype = ctypes.c_ssize_t

        style = getter(hwnd, GWL_EXSTYLE)
        style = (style | WS_EX_TOOLWINDOW) & ~WS_EX_APPWINDOW
        setter(hwnd, GWL_EXSTYLE, style)
        user32.SetWindowPos(
            hwnd, 0, 0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED | SWP_NOACTIVATE,
        )
    except Exception:
        pass
