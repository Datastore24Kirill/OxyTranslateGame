"""Read permission state without prompting; recovery is always user initiated."""
import ctypes
import subprocess
import sys
from pathlib import Path

BUNDLE_ID = 'com.oxyfire.OxyTranslateGame.Desktop'
LEGACY_BUNDLE_ID = 'com.oxyfire.OxyTranslateGame'
LSREGISTER = '/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister'

def core_graphics():
    return ctypes.CDLL('/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics')

def allowed():
    if sys.platform != 'darwin': return True
    cg = core_graphics()
    cg.CGPreflightScreenCaptureAccess.restype = ctypes.c_bool
    return bool(cg.CGPreflightScreenCaptureAccess())

def request():
    if sys.platform != 'darwin': return True
    register_current_bundle()
    cg = core_graphics()
    cg.CGRequestScreenCaptureAccess.restype = ctypes.c_bool
    return bool(cg.CGRequestScreenCaptureAccess())

def register_current_bundle():
    if sys.platform != 'darwin' or not getattr(sys, 'frozen', False): return
    bundle = next((p for p in Path(sys.executable).parents if p.suffix == '.app'), None)
    if bundle is None: return
    # Refresh the installed path: the former Swift app used a different bundle ID.
    for flag in ('-u', '-f'):
        subprocess.run([LSREGISTER, flag, str(bundle)], check=True, capture_output=True, timeout=10)

def remove_legacy_permission():
    if sys.platform != 'darwin': return
    # This obsolete ID is the same product, not another application's permission.
    subprocess.run(['/usr/bin/tccutil', 'reset', 'ScreenCapture', LEGACY_BUNDLE_ID],
                   check=False, capture_output=True, text=True, timeout=10)

def reset_current_app():
    if sys.platform != 'darwin': return
    remove_legacy_permission()
    subprocess.run(['/usr/bin/tccutil', 'reset', 'ScreenCapture', BUNDLE_ID],
                   check=True, capture_output=True, text=True, timeout=10)
