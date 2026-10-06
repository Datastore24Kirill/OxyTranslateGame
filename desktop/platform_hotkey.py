"""Native global hotkeys without a keyboard listener or accessibility permission."""

import ctypes
import itertools
import sys
from PySide6.QtCore import QObject, Signal, QAbstractNativeEventFilter

MAC_KEYS = dict(
    zip(
        "ASDFHGZXCVBQWERYT123465=97-80]OU[IP",
        [
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            19,
            20,
            21,
            23,
            22,
            24,
            26,
            28,
            25,
            29,
            27,
            30,
            31,
            32,
            33,
            34,
            35,
        ],
    )
)
MAC_KEYS.update(
    {
        "9": 25,
        "7": 26,
        "-": 27,
        "8": 28,
        "0": 29,
        "L": 37,
        "J": 38,
        "K": 40,
        "N": 45,
        "M": 46,
        "Space": 49,
        "Return": 36,
    }
)
IDS = itertools.count(0x4F58)


def parse_shortcut(sequence, platform):
    parts = sequence.split("+")
    key = parts[-1]
    mods = set(parts[:-1])
    if not mods or not mods <= {"Ctrl", "Alt", "Shift", "Meta"}:
        raise ValueError("Use Ctrl, Alt, Shift or Meta plus a letter, Space or Return")
    if len(key) == 1:
        key = key.upper()
    if platform == "darwin":
        if key not in MAC_KEYS:
            raise ValueError("Unsupported hotkey key")
        return MAC_KEYS[key], sum(
            {"Ctrl": 4096, "Alt": 2048, "Shift": 512, "Meta": 256}[m] for m in mods
        )
    if not (len(key) == 1 and key.isascii() and key.isalnum()) and key not in (
        "Space",
        "Return",
    ):
        raise ValueError("Unsupported hotkey key")
    return {"Space": 32, "Return": 13}.get(
        key, ord(key) if len(key) == 1 else 0
    ), 0x4000 | sum({"Ctrl": 2, "Alt": 1, "Shift": 4, "Meta": 8}[m] for m in mods)


class Hotkey(QObject):
    activated = Signal()

    def __init__(self, app, sequence=None):
        super().__init__()
        self.app = app
        self.ok = False
        self.key_id = next(IDS)
        self.handler = None
        code, modifiers = parse_shortcut(
            sequence or ("Meta+Alt+T" if sys.platform == "darwin" else "Ctrl+Alt+T"),
            sys.platform,
        )
        if sys.platform == "win32":
            from ctypes import wintypes

            class Filter(QAbstractNativeEventFilter):
                def nativeEventFilter(_, event_type, message):
                    msg = wintypes.MSG.from_address(int(message))
                    if msg.message == 0x0312 and msg.wParam == self.key_id:
                        self.activated.emit()
                        return True, 0
                    return False, 0

            self.filter = Filter()
            app.installNativeEventFilter(self.filter)
            self.ok = bool(
                ctypes.windll.user32.RegisterHotKey(None, self.key_id, modifiers, code)
            )
        elif sys.platform == "darwin":
            c = ctypes.CDLL("/System/Library/Frameworks/Carbon.framework/Carbon")
            self.carbon = c

            class EventType(ctypes.Structure):
                _fields_ = [("kind_class", ctypes.c_uint32), ("kind", ctypes.c_uint32)]

            class KeyID(ctypes.Structure):
                _fields_ = [("signature", ctypes.c_uint32), ("id", ctypes.c_uint32)]

            callback_type = ctypes.CFUNCTYPE(
                ctypes.c_int32, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
            )
            c.GetEventParameter.argtypes = [
                ctypes.c_void_p,
                ctypes.c_uint32,
                ctypes.c_uint32,
                ctypes.c_void_p,
                ctypes.c_uint32,
                ctypes.c_void_p,
                ctypes.c_void_p,
            ]

            def callback(_, event, __):
                found = KeyID()
                result = c.GetEventParameter(
                    event,
                    int.from_bytes(b"----", "big"),
                    int.from_bytes(b"hkid", "big"),
                    None,
                    ctypes.sizeof(found),
                    None,
                    ctypes.byref(found),
                )
                if result == 0 and found.id == self.key_id:
                    self.activated.emit()
                    return 0
                return -9874

            self.callback = callback_type(callback)
            c.GetApplicationEventTarget.restype = ctypes.c_void_p
            c.InstallEventHandler.argtypes = [
                ctypes.c_void_p,
                callback_type,
                ctypes.c_uint32,
                ctypes.POINTER(EventType),
                ctypes.c_void_p,
                ctypes.POINTER(ctypes.c_void_p),
            ]
            c.RegisterEventHotKey.argtypes = [
                ctypes.c_uint32,
                ctypes.c_uint32,
                KeyID,
                ctypes.c_void_p,
                ctypes.c_uint32,
                ctypes.POINTER(ctypes.c_void_p),
            ]
            c.UnregisterEventHotKey.argtypes = [ctypes.c_void_p]
            c.RemoveEventHandler.argtypes = [ctypes.c_void_p]
            target = c.GetApplicationEventTarget()
            self.handler = ctypes.c_void_p()
            self.key = ctypes.c_void_p()
            event = EventType(int.from_bytes(b"keyb", "big"), 6)
            installed = c.InstallEventHandler(
                target,
                self.callback,
                1,
                ctypes.byref(event),
                None,
                ctypes.byref(self.handler),
            )
            self.ok = (
                installed == 0
                and c.RegisterEventHotKey(
                    code,
                    modifiers,
                    KeyID(0x4F585947, self.key_id),
                    target,
                    0,
                    ctypes.byref(self.key),
                )
                == 0
            )

    def close(self):
        if sys.platform == "win32":
            if self.ok:
                ctypes.windll.user32.UnregisterHotKey(None, self.key_id)
            if hasattr(self, "filter"):
                self.app.removeNativeEventFilter(self.filter)
        elif sys.platform == "darwin" and hasattr(self, "carbon"):
            if self.ok:
                self.carbon.UnregisterEventHotKey(self.key)
            if self.handler:
                self.carbon.RemoveEventHandler(self.handler)
                self.handler = None
        self.ok = False
