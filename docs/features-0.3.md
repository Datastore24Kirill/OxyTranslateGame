# OxyTranslateGame 0.3 — функции и проверка / feature guide

## Языки / languages

Язык интерфейса: системный, русский, English. Он не меняет язык игры. Исходный и целевой языки: English, русский, українська, Deutsch, français, español, italiano, português, polski, 日本語, 한국어, 中文. Argos работает только при наличии прямой модели выбранной пары: проверяйте каталог. Ollama получает выбранные языки в инструкции. Автоопределение не угадывает короткие и неуверенно распознанные фразы: выберите язык вручную.

UI language is independent from translation languages. The language picker lists translation targets; it is not a claim of universal OCR support. Built-in OCR is verified for English. Review/correct the recognized original before translating other scripts. The offline catalog lists direct pairs actually available from Argos. No model or translation quality guarantee is implied.

## Профиль игры / game profile

Создайте профиль, настройте пару, режим, модель, словарь, области, тему, горячие клавиши, размер шрифта и прозрачность. Нажмите «Сохранить». JSON можно перенести на другой компьютер. Области нормализованы относительно экрана; если экран с сохранённым именем отсутствует, приложение попросит выбрать область снова. Идентификаторы окон не переносятся между сеансами — привязку к окну нужно сделать заново.

Save explicitly after changing profile settings. Import validates fields and bounds. A damaged local profile file is preserved as a recovery copy before a new store is written. Exports contain glossaries and display identifiers, but no dialogue history, API credentials or account passwords.

## Области и окно / capture and reader

До восьми областей. В режиме слежения можно переключать их по очереди; каждая реплика должна стабилизироваться перед переводом. Привязка к выбранному окну поддерживает изменение размера и перемещение в пределах текущего экрана. Свёрнутое/закрытое окно приостанавливает захват. Привязка сохраняется между запусками и следует за окном на другом мониторе. При неоднозначном совпадении названия или области, пересекающей границу экранов, захват приостанавливается. Перекрывающие игру окна могут попасть в захват: приложение снимает область экрана, а не скрытое содержимое окна.

The reader hides briefly before each capture. Click-through is reversible from the tray menu. Stop or a changed profile/region invalidates old results. Native Argos inference must finish before the worker becomes available; Ollama cancellation closes its stream once a chunk arrives (or a network timeout occurs). Closing the main window hides it and stops monitoring; use Quit in the tray to exit.

## Качество и скорость / quality and performance

Argos is the compact CPU engine. Literary/literal modes use local Ollama with three recent passages and the glossary. History storage can be disabled independently of this short in-memory context. OCR enlargement and contrast are optional. The original can be edited and translated again. Latency indicators show OCR and total elapsed time; economy mode limits capture frequency to at most once every five seconds. No paid API or automatic cloud inference is used.

## Данные и поддержка / data and support

История: поиск, лимит 10–1000 записей, CSV, отключение, явное сохранение на диск. Включение сохранения записывает текущую историю; отключение удаляет локальный history.json. CSV защищает начало ячеек от типичных формул таблиц. Словари импортируются/экспортируются отдельно.

A diagnostic ZIP includes app/OS version, architecture, screen permission status, language codes, last timings and an error category. It contains no screenshots, game dialogue, profile names or home-directory paths by default. The export dialog offers separate explicit opt-ins for current dialogue and the last selected-region image. Reports remain local until the user shares them.

## Обновления / updates

Stable is the default channel; previews are opt-in. The update dialog shows release notes in Details. Downloads verify published SHA-256 values before staging. Failed replacement restores the old application; its backup is retained after success. A crash after successful process launch is not automatically detected. macOS ad-hoc identity may require screen permission to be granted again. Apple Developer ID is deferred; SignPath Foundation declined the Windows signing application due to insufficient public visibility. Windows builds remain unsigned.

## Проверка / verification

- Automated tests: profiles/import validation/recovery, language detection, localization, history privacy, stale results, region cycling, native shortcut parsing, update integrity/swap and screen-permission behavior.
- Offscreen UI review: RU/EN, light/dark, settings and model pages. The GIF demonstrates UI states, not a benchmark of translation quality.
- Packaged application smoke test recognizes a synthetic English fixture without an external Python installation.
- Window coordinate helpers have automated tests. Real exclusive-fullscreen games, all alphabets, mixed-DPI displays, assistive technology and every game/model combination are not certified by these checks.

| Platform | Download | Runtime | Verification limits |
|---|---|---|---|
| macOS 14+ Apple Silicon | `.app` in ZIP | Bundled | OCR smoke + tests; unsigned/not notarized |
| Windows 10/11 x64 | Setup EXE / portable ZIP | Bundled | Windows CI packaging/OCR/tests; real user game test required |
| Intel Mac | No 0.3 build supplied | — | Not claimed as supported by this release |

Native window-bound APIs: [Apple CGWindowListCopyWindowInfo](https://developer.apple.com/documentation/coregraphics/cgwindowlistcopywindowinfo(_:_:)), [Microsoft IsIconic](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-isiconic).

## Изменения 0.3.1

Для японского, корейского и китайского выберите язык игры вручную, затем скачайте его OCR-модель в разделе моделей. Распознавание и перевод выполняются локально. Автоопределение не выбирает CJK-модель. Проверены три синтетических примера; корейская модель может терять пробелы и пунктуацию. Вертикальный текст и игровые шрифты требуют отдельной проверки. Модели: [RapidAI](https://github.com/RapidAI/RapidOCR/blob/main/python/rapidocr/default_models.yaml), PP-OCRv4, версия каталога 3.9.2.

Обновление показывает этап, мегабайты, скорость и время ожидания в отдельном окне. Загрузку можно отменить до установки. Если macOS отклонила старую ad-hoc подпись, кнопка восстановления сбрасывает только доступ этого приложения и после перезапуска вызывает системный запрос. Подтверждение macOS выполняет пользователь. Без Developer ID повторное разрешение после следующего обновления всё ещё возможно.
