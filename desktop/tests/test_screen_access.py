import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import screen_access

class ScreenAccessTests(unittest.TestCase):
    def test_check_does_not_request_permission(self):
        cg = Mock(); cg.CGPreflightScreenCaptureAccess.return_value = False
        with patch.object(screen_access.sys, 'platform', 'darwin'), patch.object(screen_access, 'core_graphics', return_value=cg):
            self.assertFalse(screen_access.allowed())
        cg.CGRequestScreenCaptureAccess.assert_not_called()

    def test_repair_only_resets_this_apps_screen_permission(self):
        with patch.object(screen_access.sys, 'platform', 'darwin'), patch.object(screen_access.subprocess, 'run') as run:
            screen_access.reset_current_app()
        self.assertEqual(run.call_args.args[0], ['/usr/bin/tccutil', 'reset', 'ScreenCapture', screen_access.BUNDLE_ID])

    def test_windows_never_calls_macos_api(self):
        with patch.object(screen_access.sys, 'platform', 'win32'), patch.object(screen_access, 'core_graphics') as cg:
            self.assertTrue(screen_access.allowed()); cg.assert_not_called()
