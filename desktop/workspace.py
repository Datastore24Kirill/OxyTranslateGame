"""Versioned, local profiles. Profile files never include dialogue or credentials."""

import json
import os
import uuid
from pathlib import Path
from languages import LANGUAGES

DEFAULT = {
    "source": "en",
    "target": "ru",
    "mode": 0,
    "model": "qwen3:4b",
    "glossary": "",
    "regions": [],
    "period": 2,
    "font_size": 21,
    "opacity": 100,
    "compact": False,
    "hotkeys": {},
    "theme": "system",
}


def validate_profile(value):
    if not isinstance(value, dict):
        raise ValueError("Invalid profile")
    p = {**DEFAULT, **{k: v for k, v in value.items() if k in DEFAULT}}
    if p["source"] not in ["auto", *LANGUAGES] or p["target"] not in LANGUAGES:
        raise ValueError("Invalid languages")
    if type(p["mode"]) is not int or p["mode"] not in range(3):
        raise ValueError("Invalid translation mode")
    if not isinstance(p["model"], str) or p["model"] not in ["qwen3:4b", "qwen3:8b"]:
        raise ValueError("Invalid model")
    if not isinstance(p["glossary"], str) or len(p["glossary"]) > 100000:
        raise ValueError("Invalid glossary")
    for name, low, high in [
        ("period", 1, 10),
        ("font_size", 15, 34),
        ("opacity", 45, 100),
    ]:
        if type(p[name]) is not int or not low <= p[name] <= high:
            raise ValueError("Invalid " + name)
    if not isinstance(p["regions"], list) or len(p["regions"]) > 8:
        raise ValueError("Too many regions")
    if type(p["compact"]) is not bool:
        raise ValueError("Invalid compact mode")
    if p["theme"] not in ("system", "light", "dark"):
        raise ValueError("Invalid theme")
    if not isinstance(p["hotkeys"], dict) or any(
        k not in ("region", "repeat", "stop", "reader")
        or not isinstance(v, str)
        or len(v) > 60
        for k, v in p["hotkeys"].items()
    ):
        raise ValueError("Invalid hotkeys")
    clean = []
    for r in p["regions"]:
        if (
            not isinstance(r, dict)
            or not isinstance(r.get("screen"), str)
            or not isinstance(r.get("name"), str)
        ):
            raise ValueError("Invalid region")
        rect = r.get("rect")
        if (
            not isinstance(rect, list)
            or len(rect) != 4
            or any(type(n) not in (int, float) or not 0 <= n <= 1 for n in rect)
        ):
            raise ValueError("Invalid region rectangle")
        if (
            rect[2] <= 0
            or rect[3] <= 0
            or rect[0] + rect[2] > 1.001
            or rect[1] + rect[3] > 1.001
        ):
            raise ValueError("Invalid region bounds")
        item = {"screen": r["screen"][:200], "name": r["name"][:80], "rect": rect}
        if r.get("binding"):
            binding = r["binding"]
            if (
                not isinstance(binding, dict)
                or not isinstance(binding.get("owner"), str)
                or not binding["owner"]
                or len(binding["owner"]) > 200
                or not isinstance(binding.get("title"), str)
                or len(binding["title"]) > 500
            ):
                raise ValueError("Invalid window identity")
            relative = binding.get("relative")
            if (
                not isinstance(relative, list)
                or len(relative) != 4
                or any(type(n) not in (int, float) or not 0 <= n <= 1 for n in relative)
                or relative[2] <= 0
                or relative[3] <= 0
                or relative[0] + relative[2] > 1.001
                or relative[1] + relative[3] > 1.001
            ):
                raise ValueError("Invalid window region")
            item["binding"] = {
                "owner": binding["owner"],
                "title": binding["title"],
                "relative": relative,
            }
        clean.append(item)
    p["regions"] = clean
    p["compact"] = bool(p["compact"])
    return p


class Profiles:
    def __init__(self, directory):
        self.path = Path(directory) / "profiles.json"
        self.profiles = {}
        self.current = None
        self.load_error = False
        if self.path.exists():
            try:
                self.load()
            except (ValueError, KeyError, TypeError, OSError):
                self.load_error = True
                self.profiles = {}
                self.current = None

    def load(self):
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        if (
            not isinstance(raw, dict)
            or raw.get("schema") != 1
            or not isinstance(raw.get("profiles"), dict)
        ):
            raise ValueError("Invalid profile store")
        for key, item in raw.get("profiles", {}).items():
            if len(self.profiles) >= 100:
                break
            self.profiles[key] = {
                "name": str(item["name"])[:80],
                "settings": validate_profile(item["settings"]),
            }
        self.current = (
            raw.get("current") if raw.get("current") in self.profiles else None
        )

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.load_error and self.path.exists():
            import time, shutil

            shutil.copy2(
                self.path,
                self.path.with_name(
                    "profiles-recovery-" + str(time.time_ns()) + ".json"
                ),
            )
            self.load_error = False
        temp = self.path.with_suffix(".tmp")
        temp.write_text(
            json.dumps(
                {"schema": 1, "current": self.current, "profiles": self.profiles},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        os.replace(temp, self.path)

    def create(self, name, settings):
        if not name.strip():
            raise ValueError("Profile name is required")
        if len(self.profiles) >= 100:
            raise ValueError("Profile limit reached")
        key = uuid.uuid4().hex
        self.profiles[key] = {
            "name": name.strip()[:80],
            "settings": validate_profile(settings),
        }
        self.current = key
        self.save()
        return key

    def update(self, settings):
        self.profiles[self.current]["settings"] = validate_profile(settings)
        self.save()

    def export(self, path):
        Path(path).write_text(
            json.dumps(
                {"schema": 1, **self.profiles[self.current]},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def import_file(self, path):
        if Path(path).stat().st_size > 1_000_000:
            raise ValueError("Profile file is too large")
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if data.get("schema") != 1:
            raise ValueError("Unsupported profile version")
        return self.create(str(data["name"]), data["settings"])
