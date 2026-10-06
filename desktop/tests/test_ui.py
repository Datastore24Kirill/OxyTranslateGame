"""Offscreen integration tests. No real screen capture, hotkeys or user settings."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings, QRect
import app
import i18n
from engines import LocalEngines


class UITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)
        self.settings = QSettings(str(self.path / "settings.ini"), QSettings.IniFormat)
        self.settings.setValue("onboarding/done", True)
        self.patches = [
            patch("app.QSettings", return_value=self.settings),
            patch("app.Main.check_updates"),
            patch("app.Hotkey"),
            patch("platform_hotkey.Hotkey"),
            patch("app.screen_access.allowed", return_value=True),
            patch("app.data_dir", return_value=self.path),
            patch("features.data_dir", return_value=self.path),
            patch("app.LocalEngines", return_value=LocalEngines(self.path)),
        ]
        for p in self.patches:
            p.start()
        self.w = app.Main()
        self.w.update_timer.stop()
        self.w.permission_timer.stop()

    def tearDown(self):
        self.w.stop()
        self.w.close_hotkeys()
        self.w.reader.close()
        self.w.tray.hide()
        self.w.deleteLater()
        self.qt.processEvents()
        for p in reversed(self.patches):
            p.stop()
        self.temp.cleanup()
        i18n.set_language("ru")

    def test_live_language_and_permissions(self):
        self.w.ui_language.setCurrentIndex(self.w.ui_language.findData("en"))
        self.w.refresh_permission()
        self.assertEqual(self.w.nav_buttons[0].text(), "Translate")
        self.assertEqual(self.w.permission_button.text(), "Select region")
        self.w.ui_language.setCurrentIndex(self.w.ui_language.findData("ru"))
        self.w.refresh_permission()
        self.assertEqual(self.w.nav_buttons[0].text(), "Перевод")

    def test_old_job_result_never_replaces_new_profile(self):
        token = self.w.token
        self.w.stop()
        self.w.finished(token, ("old", "stale"), "", "translate")
        self.assertEqual(self.w.preview.toPlainText(), "")
        self.assertEqual(len(self.w.history), 0)

    def test_no_history_still_has_translation_context(self):
        self.w.keep_history.setChecked(False)
        self.w.finished(self.w.token, ("hello", "привет"), "", "translate")
        self.assertEqual(len(self.w.history), 0)
        self.assertEqual(list(self.w.context), [("hello", "привет")])
        self.assertFalse((self.path / "history.json").exists())

    def test_regions_cycle_without_canceling_watch(self):
        screen = self.qt.primaryScreen()
        self.w.remember_region(screen, QRect(0, 0, 100, 100))
        self.w.remember_region(screen, QRect(100, 100, 100, 100))
        self.w.capture = lambda force: None
        self.w.all_regions.setChecked(True)
        self.w.watch.setChecked(True)
        self.w.advance_region()
        self.assertEqual(self.w.region_index, 0)
        self.assertTrue(self.w.watch.isChecked())
        self.w.area_combo.setCurrentIndex(1)
        self.assertFalse(self.w.watch.isChecked())

    def test_profile_restores_appearance_and_pair(self):
        self.w.source.setCurrentIndex(self.w.source.findData("fr"))
        self.w.reader.font_slider.setValue(29)
        self.w.profile_store.create("game", self.w.collect_profile())
        self.w.reload_profiles()
        self.w.reader.font_slider.setValue(20)
        self.w.load_profile()
        self.assertEqual(self.w.pair(), ("fr", "ru"))
        self.assertEqual(self.w.reader.font_slider.value(), 29)

    def test_history_disk_is_explicit_and_disable_deletes(self):
        self.w.history.append(("x", "y"))
        self.w.persist_history.setChecked(True)
        self.assertTrue((self.path / "history.json").exists())
        self.w.persist_history.setChecked(False)
        self.assertFalse((self.path / "history.json").exists())

    def test_compact_reader_keeps_dialogue_readable(self):
        self.w.compact_reader.setChecked(True)
        self.w.reader.text.setPlainText("A dialogue line")
        self.w.reader.show()
        self.qt.processEvents()
        self.assertGreaterEqual(self.w.reader.text.height(), 80)
        self.assertFalse(self.w.reader.reader_controls.isVisible())
        self.w.compact_reader.setChecked(False)
        self.qt.processEvents()
        self.assertTrue(self.w.reader.reader_controls.isVisible())

    def test_upgrade_permission_repair_once_and_before_restart_request(self):
        self.settings.setValue("screen/lastGrantedVersion", "0.2.7")
        with (
            patch("app.sys.platform", "darwin"),
            patch("app.screen_access.allowed", return_value=False),
            patch("app.screen_access.reset_current_app") as reset,
            patch.object(self.w, "restart_app") as restart,
            patch("app.screen_access.request", return_value=False) as request,
            patch.object(self.w, "open_screen_settings"),
        ):
            self.w.request_permission()
            reset.assert_called_once()
            restart.assert_called_once()
            request.assert_not_called()
            self.assertEqual(self.settings.value("screen/repairedVersion"), app.VERSION)
            self.w.request_permission()
            reset.assert_called_once()
            request.assert_called_once()

    def test_update_progress_visible_and_cancel_signal(self):
        from update_ui import UpdateProgress

        dialog = UpdateProgress(self.w)
        dialog.show()
        events = []
        dialog.cancel_requested.connect(lambda: events.append("cancel"))
        dialog.update_progress(
            {"stage": "download", "received": 50, "total": 100, "speed": 10}
        )
        self.assertEqual(dialog.bar.value(), 50)
        self.assertTrue(dialog.isVisible())
        dialog.cancel()
        self.assertEqual(events, ["cancel"])
        self.assertFalse(dialog.cancel_button.isEnabled())
        dialog.finish()
