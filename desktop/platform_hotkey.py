"""Native global shortcut without a keyboard listener or accessibility permission."""
import ctypes
import sys
from PySide6.QtCore import QObject, Signal, QAbstractNativeEventFilter


class Hotkey(QObject):
    activated = Signal()

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.ok = False
        if sys.platform == 'win32':
            from ctypes import wintypes
            class Filter(QAbstractNativeEventFilter):
                def nativeEventFilter(_, event_type, message):
                    msg = wintypes.MSG.from_address(int(message))
                    if msg.message == 0x0312 and msg.wParam == 0x4F58:
                        self.activated.emit(); return True, 0
                    return False, 0
            self.filter = Filter(); app.installNativeEventFilter(self.filter)
            self.ok = bool(ctypes.windll.user32.RegisterHotKey(None, 0x4F58, 0x4000 | 0x0001 | 0x0002, ord('T')))
        elif sys.platform == 'darwin':
            carbon = ctypes.CDLL('/System/Library/Frameworks/Carbon.framework/Carbon')
            self.carbon = carbon
            class EventType(ctypes.Structure):
                _fields_ = [('kind_class', ctypes.c_uint32), ('kind', ctypes.c_uint32)]
            class KeyID(ctypes.Structure):
                _fields_ = [('signature', ctypes.c_uint32), ('id', ctypes.c_uint32)]
            callback_type = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)
            self.callback = callback_type(lambda *_: (self.activated.emit(), 0)[1])
            carbon.GetApplicationEventTarget.restype = ctypes.c_void_p
            carbon.InstallEventHandler.argtypes = [ctypes.c_void_p, callback_type, ctypes.c_uint32, ctypes.POINTER(EventType), ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
            carbon.RegisterEventHotKey.argtypes = [ctypes.c_uint32, ctypes.c_uint32, KeyID, ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_void_p)]
            target = carbon.GetApplicationEventTarget(); self.handler = ctypes.c_void_p(); self.key = ctypes.c_void_p()
            event = EventType(int.from_bytes(b'keyb', 'big'), 6)
            installed = carbon.InstallEventHandler(target, self.callback, 1, ctypes.byref(event), None, ctypes.byref(self.handler))
            self.ok = installed == 0 and carbon.RegisterEventHotKey(17, 256 | 2048, KeyID(0x4F585947, 1), target, 0, ctypes.byref(self.key)) == 0

    def close(self):
        if sys.platform == 'win32' and self.ok:
            ctypes.windll.user32.UnregisterHotKey(None, 0x4F58)
        elif sys.platform == 'darwin' and self.ok:
            self.carbon.UnregisterEventHotKey(self.key)
            self.carbon.RemoveEventHandler(self.handler)
