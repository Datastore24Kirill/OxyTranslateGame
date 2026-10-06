"""Translation languages and conservative, local-only language detection."""

LANGUAGES = {
    "en": "English",
    "ru": "Русский",
    "uk": "Українська",
    "de": "Deutsch",
    "fr": "Français",
    "es": "Español",
    "it": "Italiano",
    "pt": "Português",
    "pl": "Polski",
    "ja": "日本語",
    "ko": "한국어",
    "zh": "中文",
}
NAMES = {
    "en": "English",
    "ru": "Russian",
    "uk": "Ukrainian",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "pl": "Polish",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese",
}


def validate_pair(source, target):
    if source not in LANGUAGES or target not in LANGUAGES:
        raise ValueError("Unsupported translation language")
    return source, target


def detect_source(text):
    from langdetect import detect_langs, DetectorFactory

    DetectorFactory.seed = 0
    if sum(c.isalpha() for c in text) < 20:
        raise ValueError(
            "Текст слишком короткий для определения языка. Выберите исходный язык вручную."
        )
    choices = detect_langs(text)
    if not choices or choices[0].prob < 0.90:
        raise ValueError("Язык определён неуверенно. Выберите исходный язык вручную.")
    code = choices[0].lang.split("-")[0]
    if code not in LANGUAGES:
        raise ValueError("Этот язык пока не поддерживается. Выберите язык вручную.")
    return code
