# Privacy policy

OxyTranslateGame processes the screen region selected by the user to recognize and translate text. Screenshots and recognized dialogue are not automatically uploaded to the maintainer or a cloud translation service. Screenshots are held in memory; translation history is held in memory for the current session. A user-saved glossary and application preferences are stored locally.

Network connections:

- Automatic update checks contact GitHub's API and can be disabled in Settings. GitHub receives normal connection metadata, including the IP address. Downloading an update contacts GitHub's release infrastructure.
- Installing an Argos translation model downloads the model index from GitHub and a model from the HTTPS URL specified in that index. Installation is initiated by the user.
- Literary translation sends text and recent dialogue context to Ollama at localhost (127.0.0.1). Downloading a model through Ollama contacts its model registry. Ollama is a separate installation.
- Google and Yandex buttons open the chosen service in the browser only after an explicit confirmation. The recognized text is included in that request; the screenshot is not sent. Those services apply their own privacy policies.
- Opening documentation, download links or the system browser is initiated by the user.

The application does not include analytics, advertising or automatic crash-report uploads. Installer/update logs are local. macOS screen-recording permission is controlled by the operating system; the app cannot grant itself access. Resetting a permission is limited to this product's current and former macOS identifiers.

Third-party policies: [GitHub](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement), [Google](https://policies.google.com/privacy), [Yandex](https://yandex.com/legal/confidential/), [Ollama](https://ollama.com/privacy). Component licenses are listed in [third-party notices](../desktop/THIRD_PARTY.md).

To uninstall, quit the app and remove its application bundle on macOS, or use the Windows uninstaller for the installed edition (delete the extracted folder for portable). Downloaded models, glossary and preferences remain local until the user removes them separately.
