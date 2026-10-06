"""Pinned RapidAI recognition weights; inference and character dictionaries are local."""

import hashlib
import os
import requests
from pathlib import Path
from i18n import tr

BASE = "https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.9.2/onnx/PP-OCRv4/rec/"
MODELS = {
    "ja": (
        "japan_PP-OCRv4_rec_mobile.onnx",
        "e1075a67dba758ecfc7ebc78a10ae61c95ac8fb66a9c86fab5541e33f085cb7a",
    ),
    "ko": (
        "korean_PP-OCRv4_rec_mobile.onnx",
        "ab151ba9065eccd98f884cf4d927db091be86137276392072edd4f9d43ad7426",
    ),
    "zh": (
        "ch_PP-OCRv4_rec_mobile.onnx",
        "48fc40f24f6d2a207a2b1091d3437eb3cc3eb6b676dc3ef9c37384005483683b",
    ),
}


def path_for(directory, language):
    return Path(directory) / "ocr" / MODELS[language][0]


def install(directory, language, progress, cancelled):
    if language not in MODELS:
        raise ValueError("No extra OCR model for this language")
    path = path_for(directory, language)
    path.parent.mkdir(parents=True, exist_ok=True)
    name, digest = MODELS[language]
    if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == digest:
        return
    temp = path.with_suffix(".part")
    hashed = hashlib.sha256()
    size = 0
    try:
        with requests.get(BASE + name, stream=True, timeout=(15, 30)) as response:
            response.raise_for_status()
            if not response.url.startswith("https://"):
                raise ValueError("Insecure model redirect")
            with temp.open("wb") as output:
                for chunk in response.iter_content(128 * 1024):
                    if cancelled.is_set():
                        raise InterruptedError(tr("Загрузка отменена"))
                    size += len(chunk)
                    if size > 100_000_000:
                        raise ValueError("OCR model too large")
                    output.write(chunk)
                    hashed.update(chunk)
                    progress(tr("OCR: загружено {0:.1f} МБ").format(size / 1048576))
        if hashed.hexdigest() != digest:
            raise ValueError("OCR checksum mismatch")
        if cancelled.is_set():
            raise InterruptedError(tr("Загрузка отменена"))
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)
