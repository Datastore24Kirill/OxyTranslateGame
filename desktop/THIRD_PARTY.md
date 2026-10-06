# Third-party notices

The OxyTranslateGame application source is MIT licensed. Dependencies and downloaded models retain their own licenses and are not relicensed by this repository.

- PySide6 / Qt for Python and Shiboken6: LGPLv3 / GPLv3 / commercial licensing, used as dynamically linked LGPL components. See https://doc.qt.io/qtforpython-6/licenses.html and the distributed package metadata/license files. Source and replacement builds are available from https://code.qt.io/cgit/pyside/pyside-setup.git/ and https://download.qt.io/official_releases/QtForPython/. The application does not restrict reverse engineering for debugging modifications to LGPL components; compatible dynamic libraries can be replaced in the distribution.
- langdetect: Apache-2.0 (Python port). https://github.com/Mimino666/langdetect
- RapidOCR: Apache-2.0. https://github.com/RapidAI/RapidOCR
- ONNX Runtime: MIT. https://github.com/microsoft/onnxruntime
- CTranslate2: MIT. https://github.com/OpenNMT/CTranslate2
- SentencePiece: Apache-2.0. https://github.com/google/sentencepiece
- Requests: Apache-2.0; NumPy: BSD-3-Clause; OpenCV: Apache-2.0; Pillow: HPND.
- Argos models are downloaded separately from the official package index. See the model package's metadata/README and https://github.com/argosopentech/argospm-index for provenance and model terms.
- Ollama and Qwen models are separate installations. Review their model licenses when downloading; this app does not redistribute their weights.

Build-time: PyInstaller (GPL with bootloader exception) and Inno Setup (its own license). The resulting application is not required to use their source licenses.
