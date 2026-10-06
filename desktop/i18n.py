"""Live UI localization. Game text, model IDs and profile names are never translated."""

from PySide6.QtCore import QLocale
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QCheckBox,
    QComboBox,
    QLineEdit,
    QTextEdit,
    QPlainTextEdit,
)

LANG = "ru"
EN = {
    "Перевод": "Translate",
    "Модели": "Models",
    "Имена и термины": "Names and terms",
    "История": "History",
    "Настройки": "Settings",
    "Профиль игры": "Game profile",
    "Новый": "New",
    "Сохранить": "Save",
    "Импорт": "Import",
    "Экспорт": "Export",
    "Без профиля": "No profile",
    "С какого": "From",
    "На какой": "To",
    "Определить язык": "Detect language",
    "Добавить область": "Add region",
    "Удалить область": "Remove region",
    "ПЕРЕВОД БЕЗ ГРАНИЦ": "TRANSLATION WITHOUT BORDERS",
    "Понимай историю.\nОставайся в игре.": "Follow the story.\nStay in the game.",
    "Выдели диалог — перевод появится рядом. Без скриншотов и текста в облаке.": "Select dialogue to see its translation nearby. Screenshots and text stay on your computer.",
    "＋  Выбрать область": "＋  Select region",
    "Выбрать область": "Select region",
    "Перевести снова": "Translate again",
    "Стоп": "Stop",
    "Автоматически следить за репликами": "Translate dialogue automatically",
    "Область пока не выбрана": "No region selected",
    "Готов. Выбери область экрана.": "Ready. Select a screen region.",
    "Здесь появится перевод. Отдельное окно можно перемещать и менять его размер.": "Your translation appears here. Move and resize the separate reading window.",
    "Онлайн — только по нажатию": "Online only when requested",
    "Яндекс ↗": "Yandex ↗",
    "Оригинал": "Original",
    "Копировать": "Copy",
    "Непрозрачность": "Opacity",
    "Пропускать клики": "Click through",
    "Компактно": "Compact",
    "Готов к переводу": "Ready to translate",
    "OXY / ПЕРЕВОД": "OXY / TRANSLATION",
    "ПОД ВАШУ ИГРУ": "MADE FOR YOUR GAME",
    "Оформление, перевод, доступ к экрану и обновления.": "Appearance, translation, screen access and updates.",
    "Оформление": "Appearance",
    "Системная (авто)": "System (automatic)",
    "Светлая": "Light",
    "Тёмная": "Dark",
    "Тема применяется ко всем окнам и сохраняется сразу.": "The theme applies to all windows and is saved immediately.",
    "Быстрый · локальная модель Argos": "Fast · local Argos model",
    "Литературный · локальная модель Ollama": "Literary · local Ollama model",
    "Ближе к оригиналу · Ollama": "Literal · Ollama",
    "Интервал автоматического перевода": "Automatic translation interval",
    "Доступ к экрану": "Screen access",
    "Настроить доступ": "Set up access",
    "Разрешить запись экрана": "Allow screen recording",
    "Перезапустить приложение": "Restart application",
    "Проверить доступ": "Check access",
    "Доступ включён, но не работает ▸": "Access enabled but not working ▸",
    "Скрыть дополнительные шаги ▾": "Hide troubleshooting ▾",
    "Открыть настройки macOS ↗": "Open macOS settings ↗",
    "Сбросить старое разрешение…": "Reset outdated permission…",
    "Разрешение macOS подтверждено. Можно выбрать область.": "macOS access confirmed. You can select a region.",
    "Доступ этой копии приложения пока не подтверждён.": "Access for this copy of the application is not confirmed.",
    "Нажмите «Разрешить запись экрана» и подтвердите запрос macOS. После выдачи доступа может потребоваться перезапуск.": "Click “Allow screen recording” and confirm the macOS prompt. A restart may be required.",
    "Обновления": "Updates",
    "Автоматически проверять новые версии": "Check for updates automatically",
    "Проверить обновления": "Check for updates",
    "Обновить": "Update",
    "Пропустить версию": "Skip version",
    "Позже": "Later",
    "Получать тестовые версии": "Include preview releases",
    "Сохранить технический отчёт": "Save technical report",
    "Первый запуск / помощь": "First launch / help",
    "Масштаб интерфейса": "Interface scale",
    "Экономичный режим (интервал не менее 5 секунд)": "Energy-saving mode (at least 5 seconds between captures)",
    "Увеличивать мелкий текст перед распознаванием": "Enlarge small text before recognition",
    "ДВИЖКИ ПЕРЕВОДА": "TRANSLATION ENGINES",
    "Два способа читать игру": "Two ways to read your game",
    "Первичная загрузка моделей требует интернета. Сам перевод — на твоём компьютере.": "Model downloads need internet access. Translation runs on your computer.",
    "Быстрый перевод": "Fast translation",
    "Литературный перевод": "Literary translation",
    "Компактная офлайн-модель. Подходит для меню и коротких реплик. Имена иногда переводит буквально.": "A compact offline model for menus and short dialogue. Names may be translated literally.",
    "Скачать офлайн-модель": "Download offline model",
    "Офлайн-модель установлена ✓": "Offline model installed ✓",
    "Более естественная речь и согласованные имена. Нужны Ollama и несколько гигабайт для модели. Скорость и качество зависят от компьютера.": "More natural dialogue and consistent names. Requires Ollama and several gigabytes for a model. Speed and quality depend on your computer.",
    "Установить Ollama ↗": "Install Ollama ↗",
    "Скачать выбранную модель": "Download selected model",
    "Модели не требуют API-ключа или подписки.": "No API key or subscription is required.",
    "ПОСЛЕДОВАТЕЛЬНОСТЬ": "CONSISTENCY",
    "Имена остаются именами": "Keep names consistent",
    "Словарь применяется в литературном режиме. Одна пара на строку: оригинал = перевод.": "The glossary applies to Ollama modes. One pair per line: original = translation.",
    "Сохранить словарь на этом компьютере": "Save glossary on this computer",
    "Импорт словаря": "Import glossary",
    "Экспорт словаря": "Export glossary",
    "Добавить исправление": "Add correction",
    "ТЕКУЩАЯ СЕССИЯ": "CURRENT SESSION",
    "Нить разговора": "Follow the conversation",
    "История локальна. Сохранение на диск включается отдельно.": "History stays local. Saving it to disk is optional.",
    "Очистить историю и контекст": "Clear history and context",
    "Поиск в истории": "Search history",
    "Экспорт CSV": "Export CSV",
    "Вести историю": "Keep history",
    "Сохранять историю на диске": "Save history to disk",
    "Остановлено": "Stopped",
    "Отмена… ожидаю завершения текущей операции": "Cancelling… waiting for the current operation",
    "Читаю текст…": "Reading text…",
    "Перевожу на компьютере…": "Translating locally…",
    "Перевод готов · локально": "Translation ready · local",
    "Выделение отменено": "Selection cancelled",
    "Сначала выберите область.": "Select a region first.",
    "Дождитесь завершения текущей операции или нажмите «Стоп».": "Wait for the current operation or click Stop.",
    "Текст не найден. Выделите диалог крупнее и дождитесь окончания анимации.": "No text found. Select a larger region and wait for the animation to finish.",
    "Слежение: реплика не изменилась": "Watching: dialogue has not changed",
    "Профиль сохранён": "Profile saved",
    "Словарь сохранён": "Glossary saved",
    "Модель готова. Можно переводить.": "Model ready. You can translate now.",
    "Вернуть управление окном перевода": "Restore interaction with translation window",
    "Открыть настройки": "Open settings",
    "Выход": "Quit",
    "Текст слишком короткий для определения языка. Выберите исходный язык вручную.": "Text is too short to detect the language. Select the source language manually.",
    "Язык определён неуверенно. Выберите исходный язык вручную.": "Language detection is uncertain. Select the source language manually.",
    "Этот язык пока не поддерживается. Выберите язык вручную.": "This language is not supported. Select a language manually.",
    "Технический отчёт сохранён без текста игры и снимков": "Technical report saved without game text or screenshots",
    "Клики проходят в игру. Вернуть управление можно через значок приложения в трее.": "Clicks pass through to the game. Restore interaction from the tray menu.",
}
EN.update(
    {
        " с": " s",
        " (предварительная)": " (preview)",
        "\nТекущая версия сохранена.": "\nYour current version has been preserved.",
        "Ollama · контекст трёх реплик · словарь имён": "Ollama · context of three lines · name glossary",
        "OxyTranslateGame · Перевод": "OxyTranslateGame · Translation",
        "Автообновление доступно в готовой сборке приложения.": "Automatic updates are available in the packaged application.",
        "Будет сброшено только разрешение записи экрана OxyTranslateGame. macOS попросит выдать его заново. Настройки и модели сохранятся. Продолжить?": "Only OxyTranslateGame screen recording access will be reset. macOS will request it again. Settings and models will be kept. Continue?",
        "Восстановить доступ?": "Restore access?",
        "Восстановление доступа": "Restore access",
        "Выделите текст  •  Esc — отмена": "Select text  •  Esc to cancel",
        "Горячая клавиша занята. Используйте кнопку выбора области.": "The shortcut is in use. Use the region selection button.",
        "Для загрузки выберите исходный язык вручную.": "Select the source language manually before downloading.",
        "Дождитесь завершения текущей операции перед перезапуском.": "Wait for the current operation before restarting.",
        "Доступна версия ": "Version available: ",
        "Если после обновления флажок включён, а доступ не подтверждается, сохранённое разрешение может относиться к прежней подписи. Кнопка ниже удалит эту привязку, перезапустит приложение и вызовет новый запрос macOS.": "If access is enabled after an update but the check fails, the saved permission may refer to the old signature. The button below resets this permission, restarts the app and requests access again.",
        "Запрашиваю доступ к экрану для текущей копии приложения…": "Requesting screen access for this copy of the app…",
        "Запрос отправлен macOS для этой копии приложения. Подтвердите разрешение в системном окне. Если macOS требует перезапуск, нажмите «Перезапустить приложение».": "Access was requested from macOS for this copy of the app. Confirm the system prompt. If a restart is required, click Restart application.",
        "Логотип OxyTranslateGame": "OxyTranslateGame logo",
        "Модель удалена": "Model removed",
        "Не удалось запросить доступ: ": "Could not request access: ",
        "Не удалось проверить окно игры": "Could not check the game window",
        "Не удалось проверить разрешение macOS. Повторите проверку или откройте системные настройки.": "Could not check macOS access. Retry or open System Settings.",
        "Не удалось проверить релизы. Проверьте подключение и повторите позже.": "Could not check releases. Check your connection and try again later.",
        "Не удалось сбросить разрешение. Удалите OxyTranslateGame из списка записи экрана и добавьте снова.\n": "Could not reset access. Remove OxyTranslateGame from Screen Recording and add it again.\n",
        "Не удалось снять область. Проверьте доступ к записи экрана.": "Could not capture the region. Check screen recording access.",
        "Новых готовых сборок нет.": "No new downloadable builds are available.",
        "Обновить приложение?": "Update application?",
        "Обновление": "Update",
        "Обновление готово. Ожидаю завершения текущей операции…": "Update ready. Waiting for the current operation…",
        "Обновление не установлено": "Update was not installed",
        "Остановить": "Stop",
        "Отдельное разрешение macOS на Windows не требуется.": "Windows does not require macOS screen recording permission.",
        "Открыть онлайн-переводчик?": "Open online translator?",
        "Перезапуск": "Restart",
        "Проверка разрешения macOS не нужна. Проверить захват можно через «Перевод → Выбрать область».": "No macOS permission check is needed. Test capture using Translate → Select region.",
        "Разрешение не подтверждено. После выдачи доступа перезапустите приложение. Если после обновления это не помогло, используйте восстановление ниже.": "Access is not confirmed. Restart the app after granting access. If this does not help after an update, use recovery below.",
        "Разрешение подтверждено. Нажмите «Перевод → Выбрать область».": "Access confirmed. Click Translate → Select region.",
        "Разрешение получено. Можно выбрать область.": "Access granted. You can select a region.",
        "Скачать и установить версию ": "Download and install version ",
        "? Приложение перезапустится. Модели и настройки сохранятся.": "? The app will restart. Models and settings will be kept.",
        "Сначала выделите и распознайте текст.": "Select and recognize text first.",
        "Экран отключён. Выберите область снова.": "The screen was disconnected. Select a region again.",
        "Яндекс": "Yandex",
        "Распознанный текст будет передан сервису {0} через браузер. Снимок экрана не отправляется. Продолжить?": "Recognized text will be sent to {0} through your browser. No screenshot is sent. Continue?",
        "{0} → {1}: удалить скачанную модель?": "{0} → {1}: remove the downloaded model?",
        "Выберите окно игры": "Select the game window",
        "Выбрать языковую пару": "Select language pair",
        "Доступные языковые пары": "Available language pairs",
        "Импорт профиля": "Import profile",
        "Исправьте распознанный текст и переведите снова": "Correct recognized text and translate again",
        "Модели не найдены": "No models found",
        "Модель не установлена": "Model not installed",
        "Название игры": "Game name",
        "Не более 8 областей": "Up to 8 regions are supported",
        "Не удалось зарегистрировать горячие клавиши: ": "Could not register shortcuts: ",
        "Области диалогов": "Dialogue regions",
        "Область {0}": "Region {0}",
        "Область должна находиться внутри выбранного окна": "The region must be inside the selected window",
        "Область привязана. При сворачивании окна перевод приостанавливается.": "Region attached. Translation pauses when the window is minimized.",
        "Ожидание окна игры": "Waiting for the game window",
        "Окна не найдены": "No windows found",
        "Окно перемещено на другой экран. Выберите область снова.": "The window moved to another screen. Select the region again.",
        "Оригинал = перевод": "Original = translation",
        "Отвязать окно": "Detach window",
        "Отменить загрузку": "Cancel download",
        "Первый запуск": "Getting started",
        "Показать снимок области": "Preview captured region",
        "Показать/скрыть перевод": "Show/hide translation",
        "Поменять языки местами": "Swap languages",
        "Привязать область к окну": "Attach region to window",
        "Применить горячие клавиши": "Apply shortcuts",
        "Проверить модели": "Check models",
        "Проверить оригинал": "Review original",
        "Профиль": "Profile",
        "Следить за всеми областями по очереди": "Watch all regions in sequence",
        "Снимок области — только в памяти": "Captured region — memory only",
        "Технический отчёт": "Technical report",
        "Удалить модель Ollama": "Remove Ollama model",
        "Удалить модель?": "Remove model?",
        "Удалить офлайн-модель": "Remove offline model",
        "Установлена": "Installed",
        "Экран профиля не подключён. Выберите область.": "The profile screen is not connected. Select a region.",
        "Экспорт истории": "Export history",
        "Экспорт профиля": "Export profile",
        "Ollama не запущена. Откройте вкладку «Модели» и установите Ollama.": "Ollama is not running. Open Models and install Ollama.",
        "Выберите локальную модель Ollama, без cloud.": "Select a local Ollama model, without cloud.",
        "Выберите предложенную локальную модель": "Select one of the listed local models",
        "Загрузка отменена": "Download cancelled",
        "Модель Ollama недоступна. Скачайте её во вкладке «Модели».": "Ollama model unavailable. Download it in Models.",
        "Модель вернула пустой перевод. Попробуйте другую локальную модель.": "The model returned an empty translation. Try a different local model.",
        "Модель готова. Интернет больше не нужен.": "Model ready. Internet is no longer needed.",
        "Модель имеет неподдерживаемый формат": "Unsupported model format",
        "Нет прямой модели Argos {0} → {1}. Выберите другую пару или Ollama.": "No direct Argos model for {0} → {1}. Choose a different pair or Ollama.",
        "Офлайн-модель уже установлена": "Offline model already installed",
        "Получаю список моделей Argos…": "Fetching Argos models…",
        "Сначала нажмите «Скачать офлайн-модель» во вкладке «Модели».": "Click Download offline model in Models first.",
        "Сначала установите и запустите Ollama.": "Install and start Ollama first.",
        "Загрузка модели: {0} МБ": "Downloading model: {0} MB",
        " из {0} МБ": " of {0} MB",
        "Перевод игры": "Translate your game",
        "Язык интерфейса / UI language": "UI language / Язык интерфейса",
    }
)
EN.update(
    {
        "Повышать контраст текста": "Enhance text contrast",
        "Файл профилей повреждён. Исходный файл сохранён; можно импортировать резервную копию.": "The profile file is damaged. The original is preserved; you can import a backup.",
        "Языки": "Languages",
        "Выберите язык игры и язык перевода. Интерфейс настраивается отдельно.": "Select game and translation languages. UI language is configured separately.",
        "Загрузите прямую модель для выбранной пары. Для литературного режима установите Ollama на вкладке «Модели». После загрузки перевод работает без интернета.": "Download a direct model for the selected pair. For literary translation, install Ollama from Models. Translation works offline after downloading.",
        "Разрешение требуется только для выбранной области. macOS может попросить перезапустить приложение.": "Access is used only for your selected region. macOS may ask you to restart the app.",
        "Пробный перевод": "Test translation",
        "Нажмите «Готово», затем «Выбрать область». Выделите неподвижный диалог. Распознавание проверено на английском; для других алфавитов сначала проверьте оригинал. Ошибки OCR можно исправить перед переводом.": "Click Finish, then Select region. Select dialogue after its animation finishes. OCR is verified for English; review the original for other scripts. You can correct OCR before translating.",
    }
)
EN.update({"Перевод отменён": "Translation cancelled"})
EN.update(
    {
        "По умолчанию отчёт не содержит текста игры и снимков. Файл сохраняется только на вашем компьютере.": "By default, the report contains no game text or screenshots. The file is saved only on your computer.",
        "Добавить текущий оригинал и перевод": "Include current original and translation",
        "Добавить последний снимок выбранной области": "Include last screenshot of the selected region",
        "Технический отчёт сохранён": "Technical report saved",
    }
)
EN.update(
    {
        "OCR проверено для английского. Для других языков проверьте оригинал перед переводом.": "OCR is verified for English. For other languages, review the original before translating."
    }
)
EN.update(
    {
        "Исходный язык": "Source language",
        "Язык перевода": "Target language",
        "Режим перевода": "Translation mode",
        "Модель Ollama": "Ollama model",
        "Лимит истории": "History limit",
        "Размер шрифта": "Font size",
    }
)
REVERSE = {v: k for k, v in EN.items()}


def set_language(value):
    global LANG
    LANG = (
        ("ru" if QLocale.system().name().startswith("ru") else "en")
        if value == "system"
        else value
    )


def tr(text):
    raw = REVERSE.get(text, text)
    if LANG == "ru":
        return raw
    if raw in EN:
        return EN[raw]
    for a, b in [
        ("Версия ", "Version "),
        ("Область ", "Region "),
        ("Проверено в ", "Checked at "),
    ]:
        if raw.startswith(a):
            return b + raw[len(a) :]
    return raw


def retranslate(root):
    for obj in [
        root,
        *root.findChildren(QLabel),
        *root.findChildren(QPushButton),
        *root.findChildren(QCheckBox),
    ]:
        if hasattr(obj, "text") and hasattr(obj, "setText"):
            obj.setText(tr(obj.text()))
    for combo in root.findChildren(QComboBox):
        if combo.property("userContent"):
            continue
        # Data-backed language names and profile names belong to the user.
        combo.blockSignals(True)
        for i in range(combo.count()):
            combo.setItemText(i, tr(combo.itemText(i)))
        combo.blockSignals(False)
    for edit in (
        root.findChildren(QLineEdit)
        + root.findChildren(QTextEdit)
        + root.findChildren(QPlainTextEdit)
    ):
        edit.setPlaceholderText(tr(edit.placeholderText()))
