"""Workspace controls kept separate from capture and worker lifecycle."""

import csv
import json
import platform
import sys
from pathlib import Path
from PySide6.QtCore import Qt, QRect, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QPushButton,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QLineEdit,
    QFileDialog,
    QInputDialog,
    QMessageBox,
    QCheckBox,
    QSpinBox,
)
from engines import data_dir
from languages import LANGUAGES
from workspace import Profiles, DEFAULT
from i18n import tr


class Features:
    def setup_features(self):
        self.regions = []
        self.region_index = -1
        self.last_metrics = {}
        self.last_failure = ""
        self.stable_text = ""
        self.profile_store = Profiles(data_dir())
        row = QHBoxLayout()
        row.addWidget(QLabel(tr("Профиль игры")))
        self.profile_combo = QComboBox()
        self.profile_combo.setProperty("userContent", True)
        row.addWidget(self.profile_combo, 1)
        for title, func in [
            (tr("Новый"), self.new_profile),
            (tr("Сохранить"), self.save_profile),
            (tr("Импорт"), self.import_profile),
            (tr("Экспорт"), self.export_profile),
        ]:
            b = QPushButton(title)
            b.clicked.connect(func)
            row.addWidget(b)
        self.pages.widget(0).widget().layout().insertLayout(3, row)
        row = QHBoxLayout()
        self.source = QComboBox()
        self.source.addItem(tr("Определить язык"), "auto")
        self.target = QComboBox()
        for code, name in LANGUAGES.items():
            self.source.addItem(name, code)
            self.target.addItem(name, code)
        self.source.setCurrentIndex(
            self.source.findData(self.preferences.value("translation/source", "en"))
        )
        self.target.setCurrentIndex(
            self.target.findData(self.preferences.value("translation/target", "ru"))
        )
        row.addWidget(QLabel(tr("С какого")))
        row.addWidget(self.source, 1)
        swap = QPushButton("⇄")
        swap.setAccessibleName(tr("Поменять языки местами"))
        swap.clicked.connect(self.swap_languages)
        row.addWidget(swap)
        row.addWidget(QLabel(tr("На какой")))
        row.addWidget(self.target, 1)
        self.pages.widget(0).widget().layout().insertLayout(4, row)
        self.source.currentIndexChanged.connect(self.languages_changed)
        self.target.currentIndexChanged.connect(self.languages_changed)
        row = QHBoxLayout()
        self.area_combo = QComboBox()
        self.area_combo.setProperty("userContent", True)
        self.area_combo.setPlaceholderText(tr("Области диалогов"))
        row.addWidget(self.area_combo, 1)
        for title, func in [
            (tr("Добавить область"), self.select_region),
            (tr("Удалить область"), self.remove_region),
        ]:
            b = QPushButton(title)
            b.clicked.connect(func)
            row.addWidget(b)
        self.area_combo.currentIndexChanged.connect(self.use_region)
        self.pages.widget(0).widget().layout().insertLayout(5, row)
        self.ocr_hint = QLabel(
            tr(
                "Японский, корейский и китайский требуют отдельной OCR-модели. Выберите язык игры вручную и скачайте модель."
            )
        )
        self.ocr_hint.setWordWrap(True)
        self.pages.widget(0).widget().layout().insertWidget(6, self.ocr_hint)
        self.metrics_label = QLabel("")
        self.pages.widget(0).widget().layout().addWidget(self.metrics_label)
        self.region_state = {}
        row = QHBoxLayout()
        self.pass_clicks = QCheckBox(tr("Пропускать клики"))
        self.pass_clicks.toggled.connect(self.reader_clickthrough)
        row.addWidget(self.pass_clicks)
        self.compact_reader = QCheckBox(tr("Компактно"))
        self.compact_reader.toggled.connect(self.set_compact_reader)
        row.addWidget(self.compact_reader)
        self.reader.layout().addLayout(row)
        menu = self.tray.contextMenu()
        menu.addAction(
            tr("Вернуть управление окном перевода"),
            lambda: self.pass_clicks.setChecked(False),
        )
        row = QHBoxLayout()
        self.history_search = QLineEdit()
        self.history_search.setPlaceholderText(tr("Поиск в истории"))
        self.history_search.textChanged.connect(self.render_history)
        row.addWidget(self.history_search)
        b = QPushButton(tr("Экспорт CSV"))
        b.clicked.connect(self.export_history)
        row.addWidget(b)
        self.pages.widget(3).widget().layout().insertLayout(3, row)
        row = QHBoxLayout()
        self.keep_history = QCheckBox(tr("Вести историю"))
        self.keep_history.setChecked(
            self.preferences.value("history/enabled", True, type=bool)
        )
        self.keep_history.toggled.connect(self.history_changed)
        row.addWidget(self.keep_history)
        self.persist_history = QCheckBox(tr("Сохранять историю на диске"))
        self.persist_history.setChecked(
            self.preferences.value("history/persist", False, type=bool)
        )
        self.persist_history.toggled.connect(self.history_changed)
        row.addWidget(self.persist_history)
        self.history_limit = QSpinBox()
        self.history_limit.setRange(10, 1000)
        self.history_limit.setValue(
            self.preferences.value("history/limit", 100, type=int)
        )
        self.history_limit.valueChanged.connect(self.history_changed)
        row.addWidget(self.history_limit)
        self.pages.widget(3).widget().layout().insertLayout(4, row)
        from collections import deque

        self.history = deque(self.history, maxlen=self.history_limit.value())
        path = data_dir() / "history.json"
        if (
            self.persist_history.isChecked()
            and self.keep_history.isChecked()
            and path.exists()
        ):
            try:
                entries = json.loads(path.read_text(encoding="utf-8"))
                self.history.extend(
                    (
                        (str(a), str(b))
                        for a, b in entries[-self.history_limit.value() :]
                    )
                )
            except (ValueError, TypeError):
                self.last_failure = "Could not read local history"
        self.render_history()
        row = QHBoxLayout()
        for title, func in [
            (tr("Импорт словаря"), self.import_glossary),
            (tr("Экспорт словаря"), self.export_glossary),
            (tr("Добавить исправление"), self.correct_term),
        ]:
            b = QPushButton(title)
            b.clicked.connect(func)
            row.addWidget(b)
        self.pages.widget(2).widget().layout().addLayout(row)
        settings = self.permission_status.parentWidget().parentWidget().layout()
        row = QHBoxLayout()
        self.ui_language = QComboBox()
        for title, key in [
            ("Системный / System", "system"),
            ("Русский", "ru"),
            ("English", "en"),
        ]:
            self.ui_language.addItem(title, key)
        self.ui_language.setCurrentIndex(
            max(
                0,
                self.ui_language.findData(
                    self.preferences.value("ui/language", "system")
                ),
            )
        )
        row.addWidget(QLabel(tr("Язык интерфейса / UI language")))
        row.addWidget(self.ui_language)
        settings.insertLayout(0, row)
        self.ui_language.currentIndexChanged.connect(self.change_ui_language)
        row = QHBoxLayout()
        row.addWidget(QLabel(tr("Масштаб интерфейса")))
        self.ui_scale = QSpinBox()
        self.ui_scale.setRange(80, 160)
        self.ui_scale.setSuffix("%")
        self.ui_scale.setValue(self.preferences.value("ui/scale", 100, type=int))
        self.ui_scale.valueChanged.connect(self.scale_ui)
        row.addWidget(self.ui_scale)
        settings.insertLayout(1, row)
        self.economy = QCheckBox(tr("Экономичный режим (интервал не менее 5 секунд)"))
        self.economy.setChecked(
            self.preferences.value("capture/economy", False, type=bool)
        )
        self.economy.toggled.connect(
            lambda val: self.preferences.setValue("capture/economy", val)
        )
        settings.insertWidget(2, self.economy)
        self.enhance = QCheckBox(tr("Увеличивать мелкий текст перед распознаванием"))
        self.enhance.setChecked(
            self.preferences.value("capture/enhance", True, type=bool)
        )
        self.enhance.toggled.connect(
            lambda val: self.preferences.setValue("capture/enhance", val)
        )
        settings.insertWidget(3, self.enhance)
        self.contrast = QCheckBox(tr("Повышать контраст текста"))
        self.contrast.setChecked(
            self.preferences.value("capture/contrast", False, type=bool)
        )
        self.contrast.toggled.connect(
            lambda val: self.preferences.setValue("capture/contrast", val)
        )
        settings.insertWidget(4, self.contrast)
        self.preview_updates = QCheckBox(tr("Получать тестовые версии"))
        self.preview_updates.setChecked(
            self.preferences.value("updates/preview", False, type=bool)
        )
        self.preview_updates.toggled.connect(
            lambda val: self.preferences.setValue("updates/preview", val)
        )
        settings.addWidget(self.preview_updates)
        row = QHBoxLayout()
        for title, func in [
            (tr("Сохранить технический отчёт"), self.export_diagnostics),
            (tr("Первый запуск / помощь"), self.onboarding),
        ]:
            b = QPushButton(title)
            b.clicked.connect(func)
            row.addWidget(b)
        settings.addLayout(row)
        for sequence, func in [
            ("Ctrl+Return", lambda: self.capture(True)),
            ("Ctrl+Shift+Space", self.stop),
            ("Ctrl+Shift+H", self.toggle_reader),
        ]:
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.setContext(Qt.ApplicationShortcut)
            shortcut.activated.connect(func)
        self.setup_reading_tools()
        self.setup_model_controls()
        self.setup_hotkey_controls(settings)
        for widget, title in [
            (self.source, "Исходный язык"),
            (self.target, "Язык перевода"),
            (self.profile_combo, "Профиль игры"),
            (self.area_combo, "Области диалогов"),
            (self.mode, "Режим перевода"),
            (self.model, "Модель Ollama"),
            (self.theme, "Оформление"),
            (self.history_limit, "Лимит истории"),
            (self.reader.font_slider, "Размер шрифта"),
            (self.reader.opacity_slider, "Непрозрачность"),
        ]:
            widget.setAccessibleName(tr(title))
            widget.setProperty("accessibleSource", title)
        self.reload_profiles()
        self.profile_combo.currentIndexChanged.connect(self.load_profile)
        if self.profile_store.current:
            self.load_profile()
        else:
            from workspace import validate_profile

            try:
                self.regions = validate_profile(
                    {
                        "regions": json.loads(
                            self.preferences.value("capture/regions", "[]")
                        )
                    }
                )["regions"]
                self.refresh_regions()
            except (ValueError, TypeError):
                self.regions = []
        if self.profile_store.load_error:
            self.set_status(
                tr(
                    "Файл профилей повреждён. Исходный файл сохранён; можно импортировать резервную копию."
                )
            )
        self.scale_ui()
        self.change_ui_language()
        if not self.preferences.value("onboarding/done", False, type=bool):
            QTimer.singleShot(800, self.onboarding)

    def pair(self):
        return (self.source.currentData(), self.target.currentData())

    def languages_changed(self, *_):
        self.stop()
        self.context.clear()
        self.region_state.clear()
        self.current_original = ""
        self.preview.clear()
        self.reader.text.clear()
        self.reader.original.clear()
        self.last = ""
        self.stable_text = ""
        source, target = self.pair()
        self.preferences.setValue("translation/source", source)
        self.preferences.setValue("translation/target", target)
        self.download.setText(tr(tr("Скачать офлайн-модель")))
        if hasattr(self, "catalog_text"):
            self.refresh_local_model()

    def swap_languages(self):
        source, target = self.pair()
        if source == "auto":
            return
        self.source.blockSignals(True)
        self.target.blockSignals(True)
        self.source.setCurrentIndex(self.source.findData(target))
        self.target.setCurrentIndex(self.target.findData(source))
        self.source.blockSignals(False)
        self.target.blockSignals(False)
        self.languages_changed()

    def collect_profile(self):
        return {
            **DEFAULT,
            "source": self.source.currentData(),
            "target": self.target.currentData(),
            "mode": self.mode.currentIndex(),
            "model": self.model.currentText(),
            "period": self.period.value(),
            "glossary": self.glossary.toPlainText(),
            "regions": self.regions,
            "compact": self.compact_reader.isChecked(),
            "font_size": self.reader.font_slider.value(),
            "opacity": self.reader.opacity_slider.value(),
            "hotkeys": {k: e.text() for k, e in self.hotkey_inputs.items()},
            "theme": self.theme.currentData(),
        }

    def reload_profiles(self):
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        self.profile_combo.addItem(tr("Без профиля"), None)
        for key, item in self.profile_store.profiles.items():
            self.profile_combo.addItem(item["name"], key)
        self.profile_combo.setCurrentIndex(
            max(0, self.profile_combo.findData(self.profile_store.current))
        )
        self.profile_combo.blockSignals(False)

    def new_profile(self):
        name, ok = QInputDialog.getText(self, tr("Профиль"), tr("Название игры"))
        if ok and name.strip():
            self.profile_store.create(name, self.collect_profile())
            self.reload_profiles()

    def save_profile(self):
        if not self.profile_store.current:
            return self.new_profile()
        self.profile_store.update(self.collect_profile())
        self.set_status(tr("Профиль сохранён"))

    def load_profile(self, *_):
        key = self.profile_combo.currentData()
        self.stop()
        self.context.clear()
        self.region_state.clear()
        self.current_original = ""
        self.preview.clear()
        self.reader.text.clear()
        self.reader.original.clear()
        self.last = ""
        self.profile_store.current = key
        if not key:
            self.profile_store.save()
            return
        p = self.profile_store.profiles[key]["settings"]
        self.source.setCurrentIndex(self.source.findData(p["source"]))
        self.target.setCurrentIndex(self.target.findData(p["target"]))
        self.mode.setCurrentIndex(p["mode"])
        self.model.setCurrentText(p["model"])
        self.period.setValue(p["period"])
        self.glossary.setPlainText(p["glossary"])
        self.regions = list(p["regions"])
        self.region_state.clear()
        self.window_bindings.clear()
        self.region_index = -1
        self.compact_reader.setChecked(p["compact"])
        self.reader.font_slider.setValue(p["font_size"])
        self.reader.opacity_slider.setValue(p["opacity"])
        self.theme.setCurrentIndex(self.theme.findData(p["theme"]))
        self.refresh_regions()
        self.profile_store.save()
        for k, v in p["hotkeys"].items():
            self.hotkey_inputs[k].setText(v)
        if p["hotkeys"]:
            self.apply_hotkeys()

    def import_profile(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr("Импорт профиля"), "", "JSON (*.json)"
        )
        if path:
            try:
                self.profile_store.import_file(path)
                self.reload_profiles()
                self.load_profile()
            except Exception as e:
                QMessageBox.warning(self, tr("Профиль"), str(e))

    def export_profile(self):
        if not self.profile_store.current:
            return
        self.save_profile()
        path, _ = QFileDialog.getSaveFileName(
            self, tr("Экспорт профиля"), "game-profile.json", "JSON (*.json)"
        )
        if path:
            self.profile_store.export(path)

    def remember_region(self, screen, area):
        if len(self.regions) >= 8:
            self.set_status(tr("Не более 8 областей"))
            return False
        size = screen.size()
        self.regions.append(
            {
                "name": tr("Область {0}").format(len(self.regions) + 1),
                "screen": screen.name(),
                "rect": [
                    area.x() / size.width(),
                    area.y() / size.height(),
                    area.width() / size.width(),
                    area.height() / size.height(),
                ],
            }
        )
        self.refresh_regions(len(self.regions) - 1)
        self.persist_regions()
        return True

    def refresh_regions(self, index=0):
        self.area_combo.blockSignals(True)
        self.area_combo.clear()
        for r in self.regions:
            self.area_combo.addItem(r["name"])
        self.area_combo.setCurrentIndex(index if self.regions else -1)
        self.area_combo.blockSignals(False)
        self.use_region(self.area_combo.currentIndex())

    def use_region(self, index, automatic=False):
        if not automatic:
            self.stop()
        if self.region_index >= 0:
            self.region_state[self.region_index] = (self.last, self.stable_text)
        if index < 0:
            self.region = None
            return
        r = self.regions[index]
        screen = next(
            (s for s in QApplication.screens() if s.name() == r["screen"]), None
        )
        if not screen and r.get("binding"):
            screen = QApplication.primaryScreen()
        if not screen:
            self.region = None
            self.set_status(tr("Экран профиля не подключён. Выберите область."))
            return
        x, y, w, h = r["rect"]
        size = screen.size()
        self.region = (
            screen,
            QRect(
                round(x * size.width()),
                round(y * size.height()),
                round(w * size.width()),
                round(h * size.height()),
            ),
        )
        self.region_index = index
        self.last, self.stable_text = self.region_state.get(index, ("", ""))
        self.region_label.setText(r["name"])
        self.reader_placed = False

    def remove_region(self):
        self.stop()
        i = self.area_combo.currentIndex()
        if i >= 0:
            self.regions.pop(i)
            self.region_state.clear()
            self.window_bindings.clear()
            self.region_index = -1
            self.refresh_regions()
            self.persist_regions()

    def set_compact_reader(self, yes):
        self.reader.reader_controls.setVisible(not yes)
        self.reader.opacity_controls.setVisible(not yes)
        self.reader.status.setVisible(not yes)
        self.reader.original.setVisible(
            not yes and self.reader.original_toggle.isChecked()
        )
        self.reader.resize(440 if yes else 580, 260 if yes else 390)

    def reader_clickthrough(self, yes):
        self.reader.setWindowFlag(Qt.WindowTransparentForInput, yes)
        self.reader.show()
        if yes:
            self.set_status(
                tr(
                    "Клики проходят в игру. Вернуть управление можно через значок приложения в трее."
                )
            )

    def toggle_reader(self):
        self.reader.setVisible(not self.reader.isVisible())

    def history_changed(self, *_):
        from collections import deque

        self.preferences.setValue("history/enabled", self.keep_history.isChecked())
        self.preferences.setValue("history/persist", self.persist_history.isChecked())
        self.preferences.setValue("history/limit", self.history_limit.value())
        self.history = deque(self.history, maxlen=self.history_limit.value())
        if not self.keep_history.isChecked():
            self.history.clear()
        self.render_history()
        self.write_history()

    def write_history(self):
        path = data_dir() / "history.json"
        if self.persist_history.isChecked() and self.keep_history.isChecked():
            temp = path.with_suffix(".tmp")
            temp.write_text(
                json.dumps(list(self.history), ensure_ascii=False), encoding="utf-8"
            )
            temp.replace(path)
        else:
            path.unlink(missing_ok=True)

    def render_history(self, *_):
        query = self.history_search.text().casefold()
        self.history_text.setPlainText(
            "\n\n────────────\n\n".join(
                (
                    a + "\n\n" + b
                    for a, b in reversed(self.history)
                    if query in (a + " " + b).casefold()
                )
            )
        )

    def export_history(self):
        path, _ = QFileDialog.getSaveFileName(
            self, tr("Экспорт истории"), "dialogue.csv", "CSV (*.csv)"
        )
        if path:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["Original", "Translation"])
                for a, b in self.history:
                    writer.writerow(
                        [
                            "'" + x if x.startswith(("=", "+", "-", "@")) else x
                            for x in (a, b)
                        ]
                    )

    def import_glossary(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr("Импорт словаря"), "", "Text (*.txt)"
        )
        if path and Path(path).stat().st_size <= 100000:
            self.glossary.setPlainText(Path(path).read_text(encoding="utf-8"))
            self.last = ""

    def export_glossary(self):
        path, _ = QFileDialog.getSaveFileName(
            self, tr("Экспорт словаря"), "glossary.txt", "Text (*.txt)"
        )
        if path:
            Path(path).write_text(self.glossary.toPlainText(), encoding="utf-8")

    def correct_term(self):
        value, ok = QInputDialog.getText(
            self, tr("Добавить исправление"), tr("Оригинал = перевод")
        )
        if ok and "=" in value:
            self.glossary.appendPlainText(value)
            self.save_glossary()

    def export_diagnostics(self):
        from PySide6.QtWidgets import QDialog, QDialogButtonBox
        import zipfile
        import screen_access

        dialog = QDialog(self)
        dialog.setWindowTitle(tr("Технический отчёт"))
        layout = QVBoxLayout(dialog)
        text = QLabel(
            tr(
                "По умолчанию отчёт не содержит текста игры и снимков. Файл сохраняется только на вашем компьютере."
            )
        )
        text.setWordWrap(True)
        layout.addWidget(text)
        include_text = QCheckBox(tr("Добавить текущий оригинал и перевод"))
        include_image = QCheckBox(tr("Добавить последний снимок выбранной области"))
        layout.addWidget(include_text)
        layout.addWidget(include_image)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if not dialog.exec():
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            tr("Технический отчёт"),
            "OxyTranslateGame-diagnostics.zip",
            "ZIP (*.zip)",
        )
        if not path:
            return
        from app import VERSION

        payload = {
            "schema": 1,
            "version": VERSION,
            "platform": platform.system(),
            "release": platform.release(),
            "architecture": platform.machine(),
            "screen_access": screen_access.allowed(),
            "languages": self.pair(),
            "metrics": self.last_metrics,
            "last_error_type": self.last_failure,
            "update_log_present": (data_dir() / "updates/last-install.log").exists(),
        }
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(
                "report.json", json.dumps(payload, ensure_ascii=False, indent=2)
            )
            if include_text.isChecked():
                archive.writestr(
                    "dialogue.txt",
                    self.current_original + "\n\n" + self.preview.toPlainText(),
                )
            if include_image.isChecked() and self.last_capture is not None:
                from PySide6.QtCore import QBuffer, QIODevice

                buffer = QBuffer()
                buffer.open(QIODevice.WriteOnly)
                self.last_capture.save(buffer, "PNG")
                archive.writestr("selected-region.png", bytes(buffer.data()))
        self.set_status(tr("Технический отчёт сохранён"))

    def scale_ui(self, *_):
        self.preferences.setValue("ui/scale", self.ui_scale.value())
        self.apply_theme()
        app = QApplication.instance()
        app.setStyleSheet(
            app.styleSheet()
            + f"\nQWidget {{ font-size: {round(14 * self.ui_scale.value() / 100)}px; }}"
        )

    def change_ui_language(self, *_):
        self.preferences.setValue("ui/language", self.ui_language.currentData())
        from i18n import set_language, retranslate

        set_language(self.ui_language.currentData())
        retranslate(self)
        retranslate(self.reader)
        for action in self.tray.contextMenu().actions():
            action.setText(tr(action.text()))
        self.refresh_permission()
        self.refresh_local_model()
        for root in (self, self.reader):
            from PySide6.QtWidgets import QWidget

            for widget in root.findChildren(QWidget):
                if widget.property("accessibleSource"):
                    widget.setAccessibleName(tr(widget.property("accessibleSource")))
        self.reader.setWindowTitle(tr("OxyTranslateGame · Перевод"))
        self.period.setSuffix(tr(" с"))
        self.profile_combo.setItemText(0, tr("Без профиля"))
        self.area_combo.setPlaceholderText(tr("Области диалогов"))

    def onboarding(self):
        from PySide6.QtWidgets import QWizard, QWizardPage

        wizard = QWizard(self)
        wizard.setWindowTitle(tr("Первый запуск"))
        wizard.resize(650, 420)

        def page(title, description):
            p = QWizardPage()
            p.setTitle(tr(title))
            layout = QVBoxLayout(p)
            text = QLabel(tr(description))
            text.setWordWrap(True)
            layout.addWidget(text)
            wizard.addPage(p)
            return layout

        layout = page(
            "Языки",
            "Выберите язык игры и язык перевода. Интерфейс настраивается отдельно.",
        )
        source = QComboBox()
        target = QComboBox()
        for code, name in LANGUAGES.items():
            source.addItem(name, code)
            target.addItem(name, code)
        source.setCurrentIndex(max(0, source.findData(self.source.currentData())))
        target.setCurrentIndex(max(0, target.findData(self.target.currentData())))
        layout.addWidget(source)
        layout.addWidget(target)
        source.currentIndexChanged.connect(
            lambda: self.source.setCurrentIndex(
                self.source.findData(source.currentData())
            )
        )
        target.currentIndexChanged.connect(
            lambda: self.target.setCurrentIndex(
                self.target.findData(target.currentData())
            )
        )
        layout = page(
            "Модели",
            "Загрузите прямую модель для выбранной пары. Для литературного режима установите Ollama на вкладке «Модели». После загрузки перевод работает без интернета.",
        )
        install = QPushButton(tr("Скачать офлайн-модель"))
        install.clicked.connect(self.install_fast)
        layout.addWidget(install)
        status = QLabel()
        status.setWordWrap(True)
        layout.addWidget(status)
        timer = QTimer(wizard)
        timer.timeout.connect(lambda: status.setText(self.status.text()))
        timer.start(250)
        layout = page(
            "Доступ к экрану",
            "Разрешение требуется только для выбранной области. macOS может попросить перезапустить приложение.",
        )
        allow = QPushButton(tr("Разрешить запись экрана"))
        allow.clicked.connect(self.request_permission)
        layout.addWidget(allow)
        layout = page(
            "Пробный перевод",
            "Нажмите «Готово», затем «Выбрать область». Выделите неподвижный диалог. Распознавание проверено на английском; для других алфавитов сначала проверьте оригинал. Ошибки OCR можно исправить перед переводом.",
        )
        if wizard.exec():
            self.preferences.setValue("onboarding/done", True)
            self.open_page(0)
        timer.stop()

    def setup_model_controls(self):
        layout = self.pages.widget(1).widget().layout()
        self.catalog_text = QLabel("")
        self.catalog_text.setWordWrap(True)
        layout.addWidget(self.catalog_text)
        row = QHBoxLayout()
        for title, func in [
            (tr("Проверить модели"), self.refresh_models),
            (tr("Удалить офлайн-модель"), self.remove_fast_model),
            (tr("Удалить модель Ollama"), self.remove_ollama_model),
            (tr("Отменить загрузку"), self.stop),
        ]:
            b = QPushButton(title)
            b.clicked.connect(func)
            row.addWidget(b)
        layout.addLayout(row)
        self.catalog_pairs = QComboBox()
        self.catalog_pairs.setAccessibleName(tr(tr("Доступные языковые пары")))
        layout.addWidget(self.catalog_pairs)
        choose = QPushButton(tr(tr("Выбрать языковую пару")))
        choose.clicked.connect(self.choose_catalog_pair)
        layout.addWidget(choose)
        self.ocr_status = QLabel()
        self.ocr_status.setWordWrap(True)
        layout.addWidget(self.ocr_status)
        row = QHBoxLayout()
        b = QPushButton(tr("Скачать OCR для языка игры"))
        b.clicked.connect(self.install_ocr)
        row.addWidget(b)
        b = QPushButton(tr("Удалить OCR-модель"))
        b.clicked.connect(self.remove_ocr)
        row.addWidget(b)
        layout.addLayout(row)
        self.catalog_items = []
        self.refresh_local_model()

    def refresh_local_model(self):
        source, target = self.pair()
        path = self.engine.model_path(source, target) if source != "auto" else None
        if path:
            size = sum(
                (
                    p.stat().st_size
                    for p in path.parent.parent.rglob("*")
                    if p.is_file() and (not p.is_symlink())
                )
            )
            self.catalog_text.setText(
                f"{source} → {target}: {size // 1048576} MB · " + tr(tr("Установлена"))
            )
        else:
            self.catalog_text.setText(
                f"{source} → {target}: " + tr(tr("Модель не установлена"))
            )
        if hasattr(self, "ocr_status"):
            from ocr_models import MODELS, path_for

            if source in MODELS:
                model = path_for(self.engine.directory, source)
                self.ocr_status.setText(
                    "OCR "
                    + LANGUAGES[source]
                    + ": "
                    + (
                        tr("Установлена")
                        + f" · {model.stat().st_size / 1048576:.1f} MB"
                        if model.exists()
                        else tr("Модель не установлена")
                    )
                )
            else:
                self.ocr_status.setText(
                    tr(
                        "Встроенное OCR: английский. Для японского, корейского и китайского выберите исходный язык вручную."
                    )
                )

    def install_ocr(self):
        source, _ = self.pair()
        from ocr_models import MODELS, install

        if source not in MODELS:
            self.set_status(
                tr("Выберите японский, корейский или китайский как язык игры.")
            )
            return
        self.launch_job(
            lambda progress: install(
                self.engine.directory, source, progress, self.cancel
            ),
            "install",
        )

    def remove_ocr(self):
        if self.active:
            return
        from ocr_models import MODELS, path_for

        source, _ = self.pair()
        if source not in MODELS:
            return
        if (
            QMessageBox.question(self, tr("Удалить OCR-модель"), LANGUAGES[source])
            != QMessageBox.Yes
        ):
            return
        self.engine.ocr = None
        self.engine.ocr_language = None
        path_for(self.engine.directory, source).unlink(missing_ok=True)
        self.refresh_local_model()

    def refresh_models(self):

        def work(progress):
            catalog = self.engine.catalog()
            try:
                ollama = self.engine.ollama_inventory()
            except Exception:
                ollama = []
            return (catalog, ollama)

        self.launch_job(work, "catalog")

    def remove_fast_model(self):
        if self.active:
            return
        source, target = self.pair()
        if source == "auto":
            return
        if (
            QMessageBox.question(
                self,
                tr("Удалить модель?"),
                tr("{0} → {1}: удалить скачанную модель?").format(source, target),
            )
            != QMessageBox.Yes
        ):
            return
        self.engine.remove_model(source, target)
        self.refresh_local_model()

    def remove_ollama_model(self):
        if self.active:
            return
        model = self.model.currentText()
        if QMessageBox.question(self, tr("Удалить модель?"), model) != QMessageBox.Yes:
            return
        self.launch_job(
            lambda progress: self.engine.delete_ollama(model), "remove_model"
        )

    def setup_hotkey_controls(self, layout):
        self.hotkey.close()
        self.extra_hotkeys = []
        self.hotkey_inputs = {}
        modifiers = "Meta+Alt+" if sys.platform == "darwin" else "Ctrl+Alt+"
        self.shortcut_actions = {
            "region": (tr("Выбрать область"), self.select_region, "T"),
            "repeat": (tr("Перевести снова"), lambda: self.capture(True), "R"),
            "stop": (tr("Стоп"), self.stop, "S"),
            "reader": (tr("Показать/скрыть перевод"), self.toggle_reader, "H"),
        }
        for key, (title, _, letter) in self.shortcut_actions.items():
            row = QHBoxLayout()
            row.addWidget(QLabel(title))
            edit = QLineEdit(
                self.preferences.value("hotkeys/" + key, modifiers + letter)
            )
            row.addWidget(edit)
            layout.addLayout(row)
            self.hotkey_inputs[key] = edit
        b = QPushButton(tr("Применить горячие клавиши"))
        b.clicked.connect(self.apply_hotkeys)
        layout.addWidget(b)
        self.apply_hotkeys()
        QApplication.instance().aboutToQuit.connect(self.close_hotkeys)

    def close_hotkeys(self):
        for hotkey in self.extra_hotkeys:
            hotkey.close()
        self.extra_hotkeys = []

    def apply_hotkeys(self):
        from platform_hotkey import Hotkey, parse_shortcut

        proposed = {k: e.text().strip() for k, e in self.hotkey_inputs.items()}
        try:
            parsed = [
                parse_shortcut(value, sys.platform) for value in proposed.values()
            ]
            if len(set(parsed)) != len(proposed):
                raise ValueError("Hotkeys must be different")
        except ValueError as e:
            self.set_status(str(e))
            return
        self.close_hotkeys()
        failed = []
        for key, value in proposed.items():
            h = Hotkey(QApplication.instance(), value)
            h.activated.connect(self.shortcut_actions[key][1])
            self.extra_hotkeys.append(h)
            if h.ok:
                self.preferences.setValue("hotkeys/" + key, value)
            else:
                failed.append(value)
        if failed:
            self.set_status(
                tr("Не удалось зарегистрировать горячие клавиши: ") + ", ".join(failed)
            )

    def advance_region(self):
        if (
            not self.watch.isChecked()
            or not self.all_regions.isChecked()
            or len(self.regions) < 2
        ):
            return
        index = (self.region_index + 1) % len(self.regions)
        self.area_combo.blockSignals(True)
        self.area_combo.setCurrentIndex(index)
        self.area_combo.blockSignals(False)
        self.use_region(index, automatic=True)

    def populate_catalog(self, ollama):
        self.catalog_pairs.clear()
        for p in self.catalog_items:
            self.catalog_pairs.addItem(
                LANGUAGES[p["source"]] + " → " + LANGUAGES[p["target"]],
                (p["source"], p["target"]),
            )
        self.refresh_local_model()
        self.catalog_text.setText(
            self.catalog_text.text()
            + "\nOllama: "
            + (
                ", ".join(
                    (
                        m["name"] + " (" + str(m["size"] // 1048576) + " MB)"
                        for m in ollama
                    )
                )
                or tr(tr("Модели не найдены"))
            )
        )

    def choose_catalog_pair(self):
        pair = self.catalog_pairs.currentData()
        if pair:
            self.source.setCurrentIndex(self.source.findData(pair[0]))
            self.target.setCurrentIndex(self.target.findData(pair[1]))
            self.open_page(1)

    def setup_reading_tools(self):
        self.all_regions = QCheckBox(tr(tr("Следить за всеми областями по очереди")))
        self.pages.widget(0).widget().layout().insertWidget(6, self.all_regions)
        row = QHBoxLayout()
        for title, func in [
            (tr("Проверить оригинал"), self.edit_original),
            (tr("Показать снимок области"), self.preview_capture),
        ]:
            b = QPushButton(tr(title))
            b.clicked.connect(func)
            row.addWidget(b)
        self.pages.widget(0).widget().layout().addLayout(row)
        self.last_capture = None
        self.window_bindings = {}
        row = QHBoxLayout()
        b = QPushButton(tr(tr("Привязать область к окну")))
        b.clicked.connect(self.bind_window)
        row.addWidget(b)
        b = QPushButton(tr(tr("Отвязать окно")))
        b.clicked.connect(self.detach_window)
        row.addWidget(b)
        self.pages.widget(0).widget().layout().addLayout(row)

    def edit_original(self):
        text, ok = QInputDialog.getMultiLineText(
            self,
            tr(tr("Проверить оригинал")),
            tr(tr("Исправьте распознанный текст и переведите снова")),
            self.current_original,
        )
        if not ok or not text.strip():
            return
        if self.active:
            self.set_status(
                tr(tr("Дождитесь завершения текущей операции или нажмите «Стоп»."))
            )
            return
        self.stop()
        source, target = self.pair()
        mode = self.mode.currentIndex()
        model = self.model.currentText()
        history = list(self.context)
        from engines import parse_glossary
        from languages import detect_source

        glossary = parse_glossary(self.glossary.toPlainText())

        def work(progress):
            resolved = detect_source(text) if source == "auto" else source
            return (
                text,
                self.engine.fast(text, resolved, target)
                if mode == 0
                else self.engine.literary(
                    text,
                    history,
                    glossary,
                    model,
                    resolved,
                    target,
                    mode == 2,
                    self.cancel,
                ),
            )

        self.launch_job(work)

    def preview_capture(self):
        if self.last_capture is None:
            self.set_status(tr(tr("Сначала выберите область.")))
            return
        from PySide6.QtWidgets import QDialog
        from PySide6.QtGui import QPixmap

        dialog = QDialog(self)
        dialog.setWindowTitle(tr(tr("Снимок области — только в памяти")))
        layout = QVBoxLayout(dialog)
        preview = QLabel()
        preview.setPixmap(
            QPixmap.fromImage(self.last_capture).scaled(
                900, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        )
        layout.addWidget(preview)
        dialog.exec()

    def bind_window(self):
        if not self.region:
            self.set_status(tr(tr("Сначала выберите область.")))
            return
        import window_tracking

        rows = window_tracking.windows()
        if not rows:
            self.set_status(tr(tr("Окна не найдены")))
            return
        labels = [r["name"] + " [" + str(r["id"]) + "]" for r in rows]
        choice, ok = QInputDialog.getItem(
            self,
            tr(tr("Привязать область к окну")),
            tr(tr("Выберите окно игры")),
            labels,
            0,
            False,
        )
        if not ok:
            return
        item = rows[labels.index(choice)]
        if not item.get("owner"):
            self.set_status(
                tr("Не удалось определить приложение этого окна. Выберите другое окно.")
            )
            return
        screen, rect = self.region
        origin = screen.geometry().topLeft()
        scale = screen.devicePixelRatio() if sys.platform == "win32" else 1
        if sys.platform == "win32" and item.get("monitor") != screen.name():
            self.set_status(
                tr("Окно перемещено на другой экран. Выберите область снова.")
            )
            return
        nx, ny = item.get("monitor_origin", (origin.x(), origin.y()))
        native = (
            nx + rect.x() * scale,
            ny + rect.y() * scale,
            rect.width() * scale,
            rect.height() * scale,
        )
        try:
            relative = window_tracking.relative_region(item["rect"], native)
        except ValueError:
            self.set_status(tr(tr("Область должна находиться внутри выбранного окна")))
            return
        self.stop()
        self.window_bindings[self.region_index] = {
            "id": item["id"],
            "pid": item["pid"],
            "relative": relative,
            "screen": screen.name(),
        }
        self.regions[self.region_index]["binding"] = {
            "owner": item.get("owner", ""),
            "title": item.get("title", ""),
            "relative": relative,
        }
        self.persist_regions()
        self.set_status(
            tr(
                tr(
                    "Область привязана. При сворачивании окна перевод приостанавливается."
                )
            )
        )

    def persist_regions(self):
        from workspace import validate_profile

        regions = validate_profile({"regions": self.regions})["regions"]
        self.preferences.setValue(
            "capture/regions", json.dumps(regions, ensure_ascii=False)
        )
        if self.profile_store.current:
            self.profile_store.profiles[self.profile_store.current]["settings"][
                "regions"
            ] = regions
            self.profile_store.save()

    def detach_window(self):
        self.stop()
        self.window_bindings.pop(self.region_index, None)
        if 0 <= self.region_index < len(self.regions):
            self.regions[self.region_index].pop("binding", None)
            self.persist_regions()

    def track_window(self):
        saved = (
            self.regions[self.region_index].get("binding")
            if 0 <= self.region_index < len(self.regions)
            else None
        )
        binding = self.window_bindings.get(self.region_index)
        if not saved and not binding:
            return True
        import window_tracking

        rows = window_tracking.windows()
        row = next(
            (
                r
                for r in rows
                if binding and r["id"] == binding["id"] and r["pid"] == binding["pid"]
            ),
            None,
        )
        if row is None and saved:
            row = window_tracking.match_saved_window(rows, saved)
        if row is None or not row["visible"]:
            self.set_status(tr("Ожидание окна игры"))
            return False
        relative = saved["relative"] if saved else binding["relative"]
        native = window_tracking.absolute_region(row["rect"], relative)
        if sys.platform == "win32":
            screen = next(
                (s for s in QApplication.screens() if s.name() == row.get("monitor")),
                None,
            )
            origin = row.get("monitor_origin", (0, 0))
        else:
            x, y, w, h = native
            from PySide6.QtCore import QPoint

            screen = QApplication.screenAt(QPoint(round(x + w / 2), round(y + h / 2)))
            origin = (
                (screen.geometry().x(), screen.geometry().y()) if screen else (0, 0)
            )
        if screen is None:
            self.set_status(tr("Ожидание окна игры"))
            return False
        scale = screen.devicePixelRatio() if sys.platform == "win32" else 1
        area = QRect(*window_tracking.region_on_screen(native, origin, scale))
        if not QRect(0, 0, screen.size().width(), screen.size().height()).contains(
            area
        ):
            self.set_status(
                tr(
                    "Область пересекает границу экранов. Переместите окно целиком на один экран."
                )
            )
            return False
        old = self.region
        self.region = (screen, area)
        if old is None or old[0] != screen:
            self.reader_placed = False
        self.window_bindings[self.region_index] = {
            "id": row["id"],
            "pid": row["pid"],
            "relative": relative,
            "screen": screen.name(),
        }
        return True
