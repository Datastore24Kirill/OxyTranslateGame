import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from workspace import Profiles, validate_profile
from platform_hotkey import parse_shortcut
from window_tracking import relative_region, absolute_region
from languages import detect_source


class WorkspaceTests(unittest.TestCase):
    def test_profile_roundtrip_filters_unknown_fields(self):
        with tempfile.TemporaryDirectory() as d:
            store = Profiles(d)
            store.create(
                "Example",
                {
                    "source": "de",
                    "target": "ru",
                    "font_size": 27,
                    "opacity": 70,
                    "password": "never export",
                    "hotkeys": {"repeat": "Meta+Alt+R"},
                },
            )
            path = Path(d) / "export.json"
            store.export(path)
            self.assertNotIn("password", path.read_text())
            second = Profiles(d)
            second.import_file(path)
            self.assertEqual(
                second.profiles[second.current]["settings"]["font_size"], 27
            )
            self.assertEqual(len(second.profiles), 2)

    def test_profile_rejects_unsafe_or_unbounded_input(self):
        for value in [
            {"source": "../../tmp"},
            {"mode": True},
            {"period": 999},
            {"compact": "false"},
            {"regions": [{"screen": "main", "name": "x", "rect": [0, 0, math.nan, 1]}]},
            {"regions": [{"screen": "main", "name": "x", "rect": [0.9, 0, 0.5, 1]}]},
        ]:
            with self.subTest(value=value), self.assertRaises((ValueError, TypeError)):
                validate_profile(value)

    def test_corrupt_profile_preserved_on_recovery(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "profiles.json"
            path.write_text("broken")
            store = Profiles(d)
            self.assertTrue(store.load_error)
            store.create("new", {})
            backups = list(Path(d).glob("profiles-recovery-*"))
            self.assertEqual(backups[0].read_text(), "broken")

    def test_window_resize_and_move(self):
        region = relative_region((100, 200, 1000, 500), (200, 400, 400, 100))
        self.assertEqual(
            absolute_region((300, 400, 2000, 1000), region), (500, 800, 800, 200)
        )
        with self.assertRaises(ValueError):
            relative_region((0, 0, 100, 100), (-1, 0, 20, 20))

    def test_native_shortcuts_and_equivalent_modifiers(self):
        self.assertEqual(parse_shortcut("Meta+Alt+T", "darwin"), (17, 2304))
        self.assertEqual(
            parse_shortcut("Alt+Ctrl+r", "win32"), parse_shortcut("Ctrl+Alt+R", "win32")
        )
        with self.assertRaises(ValueError):
            parse_shortcut("T", "darwin")

    def test_language_detection_short_text_refuses_guess(self):
        with self.assertRaises(ValueError):
            detect_source("Hi!")
        self.assertEqual(
            detect_source(
                "This is a long conversation about the history of our village and its people."
            ),
            "en",
        )


class SavedWindowTests(unittest.TestCase):
    def test_reacquires_new_process_but_never_ambiguous_window(self):
        from window_tracking import match_saved_window, region_on_screen

        saved = {
            "owner": "Game",
            "title": "Adventure",
            "relative": [0.1, 0.2, 0.4, 0.2],
        }
        rows = [{"owner": "Game", "title": "Adventure", "id": 25, "pid": 200}]
        self.assertEqual(match_saved_window(rows, saved)["pid"], 200)
        self.assertIsNone(match_saved_window(rows + rows, saved))
        self.assertIsNone(
            match_saved_window([{"owner": "Other", "title": "Adventure"}], saved)
        )
        self.assertEqual(
            region_on_screen((2100, 200, 800, 200), (1920, 0), 2), (90, 100, 400, 100)
        )

    def test_binding_survives_export_with_no_process_ids(self):
        value = {
            "regions": [
                {
                    "screen": "old",
                    "name": "dialogue",
                    "rect": [0, 0, 0.5, 0.5],
                    "binding": {
                        "owner": "game.exe",
                        "title": "Game",
                        "relative": [0, 0.5, 1, 0.5],
                        "pid": 456,
                    },
                }
            ]
        }
        p = validate_profile(value)
        self.assertNotIn("pid", p["regions"][0]["binding"])
        self.assertEqual(p["regions"][0]["binding"]["owner"], "game.exe")
