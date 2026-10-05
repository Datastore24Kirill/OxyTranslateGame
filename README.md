# OxyTranslateGame

**Translate a game region. Keep reading the story.**

A local-first desktop app for **macOS and Windows**, with a Russian interface and English → Russian translation. Select dialogue, get a floating translation, or watch a subtitle region automatically.

[**Download ready-to-run apps**](https://github.com/Datastore24Kirill/OxyTranslateGame/releases) · [Русская инструкция](README.ru.md) · [MIT license](LICENSE)

No source build, Python installation, subscription, or API key is needed for release downloads. The Windows release includes a normal per-user `.exe` installer and a portable ZIP. Mac releases are `.app` bundles inside ZIP files; move the app to Applications.

![OxyTranslateGame desktop interface](docs/interface.png)

## Version 0.2

- Shared dark interface for Mac and Windows, with a separate reading window.
- Move/resize the translation window; adjust font size and opacity; show the original or copy text.
- **Fast local mode:** Argos English → Russian model, downloaded once (~186 MB), running through CTranslate2.
- **Literary local mode:** optional Ollama + `qwen3:4b` or `qwen3:8b`, previous three passages as context, and a user glossary for names and terms. This requires installing Ollama and downloading a multi-GB model. Quality and speed depend on the model and hardware; human-quality localization is not guaranteed.
- In-memory session history (last 30 passages) and subtitle monitoring.
- Google / Yandex **browser buttons**, with confirmation before sending recognized text. These are not automatic or unlimited free translation APIs. No text is sent online in normal local modes.

## Start

1. Download the appropriate app from **Releases**, unzip/install, and open it. Requirements: macOS 14+ or Windows 10/11 x64. Choose the Mac build matching your processor when multiple builds are provided.
2. On Mac, allow **Screen Recording** for the app. Accessibility permission is not required. After an ad-hoc signed update, macOS may require removing the old permission entry and granting it again.
3. Open **Модели → Скачать офлайн-модель** once. Internet is needed for the download, not for later translation.
4. Press **⌥⌘T** on Mac / **Ctrl+Alt+T** on Windows, or click **Выбрать область**, then drag around dialogue. Esc cancels selection.
5. The result opens in a floating reading window. Select **Автоматически следить за репликами** for updates. The region is fixed: reselect after moving the game or changing display settings.
6. Closing the reading window stops monitoring. Closing the main window stops work and keeps the tray/menu-bar app available. Use its Exit action to quit.

### Literary mode

Install [Ollama](https://ollama.com/download) and run it. In the app's **Модели** page, select a local model and click **Скачать выбранную модель**. Choose **Литературный** on the translation page. Larger models need more RAM/VRAM and can be slow alongside a game. Start with 4B; do not assume that every machine can run 8B comfortably.

In **Имена и термины**, enter one mapping per line, such as `Mrs. Smith = миссис Смит`. Save explicitly. The glossary guides the literary model; the fast engine does not apply it. The model can still make errors, so the original remains available.

## Privacy

Selected screenshots and dialogue stay in memory and are not saved. The session history disappears on exit. Only the explicitly saved glossary and downloaded models are stored in the app's local data folder.

Fast translation runs in-process. Literary mode connects **only to `127.0.0.1:11434`**, bypasses proxy environment variables, and rejects cloud model tags. An independently configured Ollama installation is outside the app's control. Model installation downloads files from the Argos index / model host or through Ollama. Nothing is uploaded by these download actions.

Google/Yandex buttons explicitly ask before opening the recognized text in their websites. The text then leaves the computer and may enter browser history; the screenshot is not sent. These buttons are optional and separate from automatic local translation. Official Google Cloud and Yandex APIs have billing/limits and are not presented as unlimited free services.

## Limitations

OCR in this release is optimized for English source text. Small, stylized or animated text may be misread. Screen capture can fail for protected content or some exclusive-fullscreen games; try borderless/windowed mode. One selection is limited to a single monitor. The reading window briefly hides during capture so it cannot capture its own translation. Stop/cancel invalidates pending results; a running native inference/network operation may need to finish before another begins.

Preview binaries are not notarized by Apple or Authenticode-signed on Windows. OS warnings are therefore possible. Open only builds you trust; do not disable OS security globally. Packaging checks and simulated UI tests do not replace real hardware/game compatibility testing.

## For contributors (not required for users)

The cross-platform application is in `desktop/`. Use Python 3.12:

```sh
python -m venv .venv
# activate it using your platform's usual command
python -m pip install -r desktop/requirements.txt
python -m unittest discover -s desktop/tests -v
python desktop/app.py
python desktop/build.py
```

Windows installer: compile `desktop/installer.iss` with Inno Setup 6 after the PyInstaller build. GitHub Actions packages both systems and uploads ready-to-run build artifacts. Release assets are linked above.

The original macOS-only Apple Translation implementation remains in `Sources/` for reference and development (`swift test`, `scripts/build-app.sh`). Its requirements differ (macOS 15+) and it is not the cross-platform release.

See [CONTRIBUTING.md](CONTRIBUTING.md) and [third-party notices](desktop/THIRD_PARTY.md).
