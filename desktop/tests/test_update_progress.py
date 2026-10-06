import unittest, sys, tempfile, threading, hashlib
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from updater import download


class UpdateProgressTests(unittest.TestCase):
    def test_cancel_before_network(self):
        cancel = threading.Event()
        cancel.set()
        with patch("updater.urlopen") as network, self.assertRaises(InterruptedError):
            download({}, "a/b", "translator", Path("/tmp"), lambda p: None, cancel)
        network.assert_not_called()

    def test_download_emits_bytes_and_cancel_cleans_staging(self):
        class Response:
            url = "https://github.com/a/b/releases/download/v1/test.zip"

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def read(self, size):
                return b"abc"

        cancel = threading.Event()
        events = []
        asset = {
            "browser_download_url": Response.url,
            "digest": "sha256:" + hashlib.sha256(b"abcdef").hexdigest(),
            "size": 6,
        }

        def progress(value):
            events.append(value)
            if value["stage"] == "download":
                cancel.set()

        with (
            tempfile.TemporaryDirectory() as d,
            patch("updater.choose_asset", return_value=asset),
            patch("updater.urlopen", return_value=Response()),
        ):
            with self.assertRaises(InterruptedError):
                download({}, "a/b", "translator", d, progress, cancel)
            self.assertEqual(list(Path(d).iterdir()), [])
        self.assertEqual(events[0]["stage"], "connect")
        self.assertEqual(events[1]["received"], 3)
