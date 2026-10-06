"""Visible update state independent of the currently open settings page."""

import time
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton
from i18n import tr


class UpdateProgress(QDialog):
    cancel_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("Обновление"))
        self.setMinimumWidth(450)
        self.setWindowModality(Qt.WindowModal)
        self.started = time.monotonic()
        self.installing = False
        self.finished = False
        layout = QVBoxLayout(self)
        self.stage = QLabel(tr("Подключение к серверу…"))
        self.stage.setWordWrap(True)
        layout.addWidget(self.stage)
        self.bar = QProgressBar()
        self.bar.setRange(0, 0)
        layout.addWidget(self.bar)
        self.detail = QLabel()
        layout.addWidget(self.detail)
        self.elapsed = QLabel()
        layout.addWidget(self.elapsed)
        self.cancel_button = QPushButton(tr("Отменить"))
        self.cancel_button.clicked.connect(self.cancel)
        layout.addWidget(self.cancel_button)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)
        self.tick()

    def tick(self):
        self.elapsed.setText(
            tr("Прошло: {0} с").format(int(time.monotonic() - self.started))
        )

    def update_progress(self, value):
        if isinstance(value, str):
            self.stage.setText(tr(value))
            return
        stage = value.get("stage", "download")
        labels = {
            "connect": "Подключение к серверу…",
            "download": "Скачивание обновления",
            "verify": "Проверка контрольной суммы…",
            "extract": "Распаковка обновления…",
            "stage": "Подготовка установки…",
            "wait": "Ожидание завершения перевода…",
            "install": "Установка и перезапуск…",
        }
        self.stage.setText(tr(labels.get(stage, stage)))
        if stage == "download":
            total = value["total"]
            done = value["received"]
            self.bar.setRange(0, 100)
            self.bar.setValue(min(100, int(done * 100 / total)))
            self.detail.setText(
                tr("{0:.1f} / {1:.1f} МБ · {2:.1f} МБ/с").format(
                    done / 1048576, total / 1048576, value.get("speed", 0) / 1048576
                )
            )
        else:
            self.bar.setRange(0, 0)
        if stage == "install":
            self.installing = True
            self.cancel_button.setEnabled(False)

    def cancel(self):
        if self.installing:
            return
        self.cancel_button.setEnabled(False)
        self.stage.setText(tr("Отмена… ожидаю завершения текущей операции"))
        self.cancel_requested.emit()

    def reject(self):
        if self.finished:
            super().reject()
        else:
            self.cancel()

    def finish(self):
        self.finished = True
        self.timer.stop()
        self.accept()
