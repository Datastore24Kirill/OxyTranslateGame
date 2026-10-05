# Contributing

Use Xcode 16+ / Swift 6 and macOS 15+. Run `swift test` and `./scripts/build-app.sh` before sending a pull request. Keep captures and recognized text out of commits and crash reports by default.

For capture/selection changes, manually check: reverse-direction selection, Retina display, non-primary display, Escape cancellation, game behind the overlay, stopping during OCR/translation, and disconnecting the selected display. For translation changes, check first-time language download, cancellation, unsupported pairs, and repeated unchanged subtitles.

Do not commit signing identities, provisioning profiles, API keys, local logs or personal game screenshots. Report issues with concise reproduction steps; add screenshots only after checking their contents.
