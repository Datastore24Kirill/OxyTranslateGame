"""Read window bounds only; never move windows or inspect their contents."""

import ctypes
import os
import plistlib
import sys


def windows():
    if sys.platform == "darwin":
        cg = ctypes.CDLL(
            "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics"
        )
        cf = ctypes.CDLL(
            "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation"
        )
        cg.CGWindowListCopyWindowInfo.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
        cg.CGWindowListCopyWindowInfo.restype = ctypes.c_void_p
        cf.CFPropertyListCreateData.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_ulong,
            ctypes.c_void_p,
        ]
        cf.CFPropertyListCreateData.restype = ctypes.c_void_p
        cf.CFDataGetLength.argtypes = [ctypes.c_void_p]
        cf.CFDataGetLength.restype = ctypes.c_long
        cf.CFDataGetBytePtr.argtypes = [ctypes.c_void_p]
        cf.CFDataGetBytePtr.restype = ctypes.c_void_p
        cf.CFRelease.argtypes = [ctypes.c_void_p]
        ref = cg.CGWindowListCopyWindowInfo(16, 0)
        if not ref:
            return []
        data = None
        try:
            data = cf.CFPropertyListCreateData(None, ref, 200, 0, None)
            if not data:
                return []
            rows = plistlib.loads(
                ctypes.string_at(cf.CFDataGetBytePtr(data), cf.CFDataGetLength(data))
            )
        finally:
            if data:
                cf.CFRelease(data)
            cf.CFRelease(ref)
        result = []
        for r in rows:
            b = r.get("kCGWindowBounds", {})
            if (
                r.get("kCGWindowLayer") != 0
                or r.get("kCGWindowOwnerPID") == os.getpid()
                or b.get("Width", 0) < 100
                or b.get("Height", 0) < 80
            ):
                continue
            result.append(
                {
                    "id": r["kCGWindowNumber"],
                    "pid": r["kCGWindowOwnerPID"],
                    "owner": r.get("kCGWindowOwnerName", "")[:200],
                    "title": r.get("kCGWindowName", "")[:500],
                    "name": r.get("kCGWindowOwnerName", "")
                    + " — "
                    + r.get("kCGWindowName", ""),
                    "rect": (b["X"], b["Y"], b["Width"], b["Height"]),
                    "visible": bool(r.get("kCGWindowIsOnscreen")),
                }
            )
        return result
    if sys.platform == "win32":
        from ctypes import wintypes as w

        u = ctypes.windll.user32
        result = []
        callback = ctypes.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
        u.GetWindowRect.argtypes = [w.HWND, ctypes.POINTER(w.RECT)]
        u.GetWindowTextW.argtypes = [w.HWND, w.LPWSTR, ctypes.c_int]
        u.GetWindowThreadProcessId.argtypes = [w.HWND, ctypes.POINTER(w.DWORD)]
        u.IsWindowVisible.argtypes = [w.HWND]
        u.IsIconic.argtypes = [w.HWND]

        class MonitorInfo(ctypes.Structure):
            _fields_ = [
                ("cbSize", w.DWORD),
                ("rcMonitor", w.RECT),
                ("rcWork", w.RECT),
                ("dwFlags", w.DWORD),
                ("szDevice", w.WCHAR * 32),
            ]

        u.MonitorFromWindow.argtypes = [w.HWND, w.DWORD]
        u.MonitorFromWindow.restype = w.HANDLE
        u.GetMonitorInfoW.argtypes = [w.HANDLE, ctypes.POINTER(MonitorInfo)]

        kernel = ctypes.windll.kernel32
        kernel.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
        kernel.OpenProcess.restype = w.HANDLE
        kernel.QueryFullProcessImageNameW.argtypes = [
            w.HANDLE,
            w.DWORD,
            w.LPWSTR,
            ctypes.POINTER(w.DWORD),
        ]
        kernel.CloseHandle.argtypes = [w.HANDLE]

        @callback
        def each(hwnd, _):
            pid = w.DWORD()
            u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            title = ctypes.create_unicode_buffer(1024)
            u.GetWindowTextW(hwnd, title, 1024)
            if not title.value or pid.value == os.getpid():
                return True
            owner = ""
            handle = kernel.OpenProcess(0x1000, False, pid.value)
            if handle:
                try:
                    buffer = ctypes.create_unicode_buffer(32768)
                    length = w.DWORD(len(buffer))
                    if kernel.QueryFullProcessImageNameW(
                        handle, 0, buffer, ctypes.byref(length)
                    ):
                        from pathlib import PureWindowsPath

                        owner = PureWindowsPath(buffer.value).name.casefold()
                finally:
                    kernel.CloseHandle(handle)
            monitor = MonitorInfo()
            monitor.cbSize = ctypes.sizeof(monitor)
            u.GetMonitorInfoW(u.MonitorFromWindow(hwnd, 2), ctypes.byref(monitor))
            rect = w.RECT()
            if u.GetWindowRect(hwnd, ctypes.byref(rect)):
                result.append(
                    {
                        "id": int(hwnd),
                        "pid": pid.value,
                        "name": title.value,
                        "owner": owner,
                        "title": title.value[:500],
                        "monitor": monitor.szDevice,
                        "monitor_origin": (
                            monitor.rcMonitor.left,
                            monitor.rcMonitor.top,
                        ),
                        "rect": (
                            rect.left,
                            rect.top,
                            rect.right - rect.left,
                            rect.bottom - rect.top,
                        ),
                        "visible": bool(
                            u.IsWindowVisible(hwnd) and not u.IsIconic(hwnd)
                        ),
                    }
                )
            return True

        u.EnumWindows.argtypes = [callback, w.LPARAM]
        u.EnumWindows(each, 0)
        return result
    return []


def relative_region(window, region):
    x, y, w, h = window
    rx, ry, rw, rh = region
    if (
        w <= 0
        or h <= 0
        or rx < x
        or ry < y
        or rx + rw > x + w + 1
        or ry + rh > y + h + 1
    ):
        raise ValueError("Region must be inside the selected window")
    return [(rx - x) / w, (ry - y) / h, rw / w, rh / h]


def absolute_region(window, relative):
    x, y, w, h = window
    rx, ry, rw, rh = relative
    return (
        round(x + rx * w),
        round(y + ry * h),
        max(1, round(rw * w)),
        max(1, round(rh * h)),
    )


def match_saved_window(rows, binding):
    """Never guess between windows with the same saved identity."""
    matches = [
        r
        for r in rows
        if r.get("owner") == binding.get("owner")
        and r.get("title") == binding.get("title")
        and r.get("owner")
    ]
    return matches[0] if len(matches) == 1 else None


def region_on_screen(native, origin, scale):
    x, y, w, h = native
    ox, oy = origin
    if scale <= 0:
        raise ValueError("Invalid scale")
    return (
        round((x - ox) / scale),
        round((y - oy) / scale),
        max(1, round(w / scale)),
        max(1, round(h / scale)),
    )
