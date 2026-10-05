# OxyTranslateGame

A small native macOS app that translates text from any selected screen region. Built for games, useful in other apps too. Russian interface; English → Russian by default.

**macOS 15 or newer.** Uses Apple Vision for OCR, ScreenCaptureKit for capture, and Apple's on-device Translation framework. No API keys, paid translation service, Python runtime, or external packages.

## Use

1. Open the app and allow **Screen Recording** in System Settings → Privacy & Security. Relaunch if macOS requests it.
2. Choose the source and target languages. Click **Подготовить языки** to download the Apple language models once; this requires an internet connection and system approval.
3. While in a game, press **⌥⌘T**, then drag around the dialogue or menu. **Esc** cancels selection.
4. Read the translation in a floating, movable, resizable window. The **Оригинал** checkbox shows recognized text alongside the translation.
5. Enable **Следить за областью** in the main window to refresh when text changes. Choose a 1, 2, or 4 second interval.
6. Stop from the main window, result window, or menu-bar menu. **Esc** closes the result when it has keyboard focus.

The alternate selection shortcut is **⇧⌥⌘T**. Closing the main window keeps the menu-bar app running; use **⌘Q** to quit.

A region belongs to one display. Reselect after moving/resizing the game, changing resolution, or disconnecting a monitor. The app excludes its own windows from capture. It does not click in games or modify game files.

## Build

Install Xcode 16 or newer and select its developer tools, then:

```sh
swift test
./scripts/build-app.sh
open dist/OxyTranslateGame.app
```

The script creates a native-architecture `.app` and ZIP in `dist/`. Build for another architecture with `./scripts/build-app.sh --arch x86_64` (or `arm64`). CI checks builds on macOS; hardware-specific behavior still needs live testing.

Local builds are ad-hoc signed by default, **not notarized**. For distribution, supply your own signing identity via `CODESIGN_IDENTITY` and notarize with your Apple Developer account. A downloaded development build may require **Open Anyway** in Privacy & Security. Never disable Gatekeeper system-wide. Ad-hoc rebuilds can invalidate old screen permissions; remove the old app entry and grant access to the new build if macOS shows an enabled but ineffective permission.

## Privacy

Screenshots are processed in memory, only for the chosen region, and are not saved. Recognized text, translations, and a bounded translation cache are memory-only. The app does not send screenshots or text to third-party translation APIs. Apple states translations are processed on-device; Apple may collect framework usage/performance metadata. See [Apple TranslationSession documentation](https://developer.apple.com/documentation/translation/translationsession).

Only Screen Recording is required. Global selection hotkeys use the macOS hotkey API; Accessibility / Input Monitoring is not requested. The clipboard is changed only when you click **Копировать**. Errors are written through the system logger; screenshots and recognized text are not deliberately included in logs.

## Limitations

- OCR can misread animated, tiny, decorative, or low-contrast text. Select the text closely and wait for animations to settle.
- Translation quality, supported language pairs, and model downloads are controlled by Apple. The app checks language-pair availability and reports unsupported pairs.
- Screen recording permission, DRM-protected content, exclusive fullscreen games, and overlays can affect capture. Windowed/borderless mode is recommended if selection is unavailable.
- The selected rectangle is fixed; the app does not track moving game windows.
- This first release does not replace the original text inside the game or guarantee every game's compatibility.

## Contributing

Issues and pull requests are welcome. Include macOS version, app version, source/target languages, display scaling, and reproduction steps. Please avoid private screenshots or dialogue unless you intentionally want to publish them. See [CONTRIBUTING.md](CONTRIBUTING.md).

[Русская инструкция](README.ru.md) · [MIT license](LICENSE)
