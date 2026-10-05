"""Read permission state without prompting; recovery is always user initiated."""
import ctypes
import subprocess
import sys

BUNDLE_ID = 'com.oxyfire.OxyTranslateGame.Desktop'

def core_graphics():
    return ctypes.CDLL('/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics')

def allowed():
    if sys.platform != 'darwin': return True
    cg = core_graphics()
    cg.CGPreflightScreenCaptureAccess.restype = ctypes.c_bool
    return bool(cg.CGPreflightScreenCaptureAccess())

def request():
    if sys.platform != 'darwin': return True
    cg = core_graphics()
    cg.CGRequestScreenCaptureAccess.restype = ctypes.c_bool
    return bool(cg.CGRequestScreenCaptureAccess())

def reset_current_app():
    if sys.platform != 'darwin': return
    subprocess.run(['/usr/bin/tccutil', 'reset', 'ScreenCapture', BUNDLE_ID],
                   check=True, capture_output=True, text=True, timeout=10)
