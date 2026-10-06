import subprocess
import os
import sys
import threading
import time
from collections import deque
from pathlib import Path
from urllib.parse import urlencode
from PySide6.QtCore import (
    Qt,
    QRect,
    Signal,
    QObject,
    QRunnable,
    QThreadPool,
    QTimer,
    QUrl,
    QSettings,
)
from PySide6.QtGui import (
    QColor,
    QPainter,
    QPen,
    QFont,
    QKeySequence,
    QShortcut,
    QDesktopServices,
    QIcon,
    QImage,
    QPalette,
)
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QStackedWidget,
    QComboBox,
    QTextEdit,
    QPlainTextEdit,
    QCheckBox,
    QSlider,
    QSpinBox,
    QMessageBox,
    QProgressBar,
    QSystemTrayIcon,
    QMenu,
    QScrollArea,
)
from engines import LocalEngines, data_dir, normalize, parse_glossary
from platform_hotkey import Hotkey
from theme import stylesheet
import screen_access
from releases import check_release
from features import Features
from languages import detect_source
from i18n import tr
from updater import download, mac_bundle, stage_replacement, launch_swap

VERSION = "0.3.1"


class Signals(QObject):
    done = Signal(int, object, str)
    progress = Signal(int, object)
    recognized = Signal(int, str)


class Job(QRunnable):
    def __init__(self, token, function):
        super().__init__()
        self.token = token
        self.function = function
        self.signals = Signals()

    def run(self):
        try:
            self.signals.done.emit(
                self.token,
                self.function(
                    lambda text: self.signals.progress.emit(self.token, text)
                ),
                "",
            )
        except Exception as error:
            self.signals.done.emit(self.token, None, str(error))


def button(text, action=None, primary=False):
    result = QPushButton(tr(text))
    if primary:
        result.setObjectName("Primary")
    if action:
        result.clicked.connect(action)
    return result


def label(text, style=None):
    widget = QLabel(tr(text))
    widget.setWordWrap(True)
    if style:
        widget.setObjectName(style)
    return widget


def card():
    frame = QFrame()
    frame.setObjectName("Card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(22, 20, 22, 20)
    layout.setSpacing(12)
    return (frame, layout)


class Selector(QWidget):
    selected = Signal(object, object)
    cancelled = Signal()

    def __init__(self, screen):
        super().__init__(
            None, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.screen = screen
        self.origin = None
        self.area = QRect()
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(screen.geometry())
        self.setCursor(Qt.CrossCursor)
        self.setMouseTracking(True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(5, 14, 26, 115))
        if not self.area.isNull():
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(self.area, Qt.transparent)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.setPen(QPen(QColor("#66e0bd"), 2))
            painter.drawRect(self.area)
        painter.setPen(Qt.white)
        painter.setFont(QFont("Arial", 17))
        painter.drawText(28, 44, tr("Выделите текст  •  Esc — отмена"))

    def mousePressEvent(self, event):
        self.origin = event.position().toPoint()

    def mouseMoveEvent(self, event):
        if self.origin is not None:
            self.area = (
                QRect(self.origin, event.position().toPoint())
                .normalized()
                .intersected(self.rect())
            )
            self.update()

    def mouseReleaseEvent(self, event):
        self.mouseMoveEvent(event)
        if self.area.width() >= 20 and self.area.height() >= 20:
            self.selected.emit(self.screen, self.area)
        else:
            self.cancelled.emit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.cancelled.emit()


class Reader(QWidget):
    closed = Signal()

    def __init__(self, owner):
        super().__init__(None, Qt.Tool | Qt.WindowStaysOnTopHint)
        self.owner = owner
        self.setWindowTitle(tr("OxyTranslateGame · Перевод"))
        self.resize(580, 330)
        self.setMinimumSize(390, 240)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        head = QHBoxLayout()
        head.addWidget(label(tr("OXY / ПЕРЕВОД"), "Eyebrow"))
        head.addStretch()
        head.addWidget(button(tr("Настройки"), owner.show_settings))
        head.addWidget(button("✕", self.close))
        layout.addLayout(head)
        self.status = label(tr("Готов к переводу"), "Muted")
        layout.addWidget(self.status)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setStyleSheet(
            "font-size: 21px; border: none; background: transparent;"
        )
        layout.addWidget(self.text, 1)
        self.original = QTextEdit()
        self.original.setReadOnly(True)
        self.original.setMaximumHeight(120)
        self.original.hide()
        layout.addWidget(self.original)
        row = QHBoxLayout()
        self.original_toggle = QCheckBox(tr("Оригинал"))
        self.original_toggle.toggled.connect(self.original.setVisible)
        row.addWidget(self.original_toggle)
        row.addWidget(
            button(
                tr("Копировать"),
                lambda: QApplication.clipboard().setText(self.text.toPlainText()),
            )
        )
        row.addStretch()
        row.addWidget(label("A"))
        font = self.font_slider = QSlider(Qt.Horizontal)
        font.setRange(15, 34)
        font.setValue(owner.preferences.value("reader/font", 21, type=int))
        font.setMaximumWidth(95)
        font.valueChanged.connect(
            lambda size: self.text.setStyleSheet(
                f"font-size: {size}px; border: none; background: transparent;"
            )
        )
        font.valueChanged.connect(
            lambda n: owner.preferences.setValue("reader/font", n)
        )
        self.text.setStyleSheet(
            f"font-size: {font.value()}px; border: none; background: transparent;"
        )
        row.addWidget(font)
        self.reader_controls = QWidget()
        self.reader_controls.setLayout(row)
        layout.addWidget(self.reader_controls)
        opacity = self.opacity_slider = QSlider(Qt.Horizontal)
        opacity.setRange(45, 100)
        opacity.setValue(owner.preferences.value("reader/opacity", 100, type=int))
        opacity.setMaximumWidth(130)
        opacity.valueChanged.connect(lambda value: self.setWindowOpacity(value / 100))
        opacity.valueChanged.connect(
            lambda n: owner.preferences.setValue("reader/opacity", n)
        )
        self.setWindowOpacity(opacity.value() / 100)
        row2 = QHBoxLayout()
        row2.addWidget(label(tr("Непрозрачность"), "Muted"))
        row2.addWidget(opacity)
        row2.addStretch()
        self.opacity_controls = QWidget()
        self.opacity_controls.setLayout(row2)
        layout.addWidget(self.opacity_controls)
        QShortcut(QKeySequence("Escape"), self, activated=self.close)

    def closeEvent(self, event):
        self.closed.emit()
        event.accept()


class Main(QMainWindow, Features):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OxyTranslateGame")
        self.resize(1020, 780)
        self.setMinimumSize(760, 560)
        self.preferences = QSettings()
        self.update_job = None
        self.update_info = None
        self.update_later_until = 0
        self.permission_requested = False
        self.install_job = None
        self.engine = LocalEngines()
        self.pool = QThreadPool()
        self.pool.setMaxThreadCount(1)
        self.token = 0
        self.active = None
        self.cancel = threading.Event()
        self.region = None
        self.selectors = []
        self.history = deque(maxlen=30)
        self.last = ""
        self.context = deque(maxlen=3)
        self.current_original = ""
        self.capture_pending = False
        self.reader_placed = False
        self.reader = Reader(self)
        self.reader.closed.connect(self.stop)
        root = QWidget()
        self.setCentralWidget(root)
        base = QHBoxLayout(root)
        base.setContentsMargins(0, 0, 0, 0)
        base.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(214)
        nav = QVBoxLayout(sidebar)
        nav.setContentsMargins(22, 30, 18, 25)
        icon_path = (
            Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / "AppIcon.png"
        )
        brand_icon = QLabel()
        brand_icon.setPixmap(QIcon(str(icon_path)).pixmap(76, 76))
        brand_icon.setAccessibleName(tr("Логотип OxyTranslateGame"))
        nav.addWidget(brand_icon)
        nav.addWidget(label("Oxy\nTranslateGame", "Brand"))
        nav.addWidget(label("YOUR GAME. YOUR LANGUAGE.", "Eyebrow"))
        nav.addSpacing(30)
        self.pages = QStackedWidget()
        self.nav_buttons = []
        for index, title in enumerate(
            [
                tr("Перевод"),
                tr("Модели"),
                tr("Имена и термины"),
                tr("История"),
                tr("Настройки"),
            ]
        ):
            item = button(title, lambda checked=False, n=index: self.open_page(n))
            item.setObjectName("Nav")
            item.setCheckable(True)
            nav.addWidget(item)
            self.nav_buttons.append(item)
        nav.addStretch()
        self.update_notice = label("", "Muted")
        self.update_notice.hide()
        nav.addWidget(self.update_notice)
        self.update_open = button(tr("Обновить"), self.open_update)
        self.update_open.hide()
        nav.addWidget(self.update_open)
        self.update_skip = button(tr("Пропустить версию"), self.skip_update)
        self.update_skip.hide()
        nav.addWidget(self.update_skip)
        self.update_later = button(tr("Позже"), self.defer_update)
        self.update_later.hide()
        nav.addWidget(self.update_later)
        nav.addWidget(label("●  LOCAL FIRST", "Eyebrow"))
        nav.addWidget(label("Mac + Windows\nv" + VERSION, "Muted"))
        base.addWidget(sidebar)
        base.addWidget(self.pages, 1)
        self.build_translate()
        self.build_models()
        self.build_glossary()
        self.build_history()
        self.build_settings()
        self.open_page(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda: self.capture(False))
        self.hotkey = Hotkey(QApplication.instance())
        self.hotkey.activated.connect(self.select_region)
        if not self.hotkey.ok:
            self.set_status(
                tr("Горячая клавиша занята. Используйте кнопку выбора области.")
            )
        self.tray = QSystemTrayIcon(self)
        icon_path = (
            Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / "AppIcon.png"
        )
        if icon_path.exists():
            app_icon = QIcon(str(icon_path))
            QApplication.instance().setWindowIcon(app_icon)
            self.setWindowIcon(app_icon)
            self.reader.setWindowIcon(app_icon)
            self.tray.setIcon(app_icon)
        menu = QMenu()
        menu.addAction(tr("Выбрать область"), self.select_region)
        menu.addAction(tr("Остановить"), self.stop)
        menu.addAction(tr("Открыть настройки"), self.show_settings)
        menu.addAction(tr("Выход"), self.quit)
        menu.addAction(tr("Проверить обновления"), lambda: self.check_updates(True))
        self.tray.setContextMenu(menu)
        self.tray.show()
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.check_updates)
        self.update_timer.start(6 * 60 * 60 * 1000)
        QApplication.instance().styleHints().colorSchemeChanged.connect(
            lambda _: self.apply_theme()
        )
        self.apply_theme()
        if self.preferences.value("screen/requestAfterRestart", False, type=bool):
            self.preferences.remove("screen/requestAfterRestart")
            QTimer.singleShot(500, self.request_permission)
        self.permission_timer = QTimer(self)
        self.permission_timer.timeout.connect(self.refresh_permission)
        self.permission_timer.start(2000)
        self.setup_features()
        QTimer.singleShot(12000, self.check_updates)

    def check_updates(self, manual=False):
        if self.update_job or (
            not manual
            and (
                not self.auto_updates.isChecked()
                or time.monotonic() < self.update_later_until
            )
        ):
            return
        self.update_job = Job(
            0,
            lambda progress: check_release(
                "Datastore24Kirill/OxyTranslateGame",
                VERSION,
                allow_preview=self.preferences.value(
                    "updates/preview", False, type=bool
                ),
            ),
        )
        self.update_job.signals.done.connect(
            lambda token, info, error: self.update_checked(info, error, manual)
        )
        QThreadPool.globalInstance().start(self.update_job)

    def update_checked(self, info, error, manual):
        self.update_job = None
        if error:
            if manual:
                QMessageBox.information(
                    self,
                    tr("Обновления"),
                    tr(
                        "Не удалось проверить релизы. Проверьте подключение и повторите позже."
                    ),
                )
            return
        if not info:
            if manual:
                QMessageBox.information(
                    self, tr("Обновления"), tr("Новых готовых сборок нет.")
                )
            return
        if (
            not manual
            and self.preferences.value("updates/skipped", "") == info["latest"]
        ):
            return
        self.update_info = info
        self.update_notice.setText(
            tr("Доступна версия ")
            + info["latest"]
            + (tr(" (предварительная)") if info["preview"] else "")
        )
        self.update_notice.show()
        self.update_open.show()
        self.update_skip.show()
        self.update_later.show()

    def open_update(self):
        if not self.update_info or self.install_job:
            return
        try:
            if not getattr(sys, "frozen", False):
                raise RuntimeError(
                    tr("Автообновление доступно в готовой сборке приложения.")
                )
            target = (
                mac_bundle(sys.executable)
                if sys.platform == "darwin"
                else Path(sys.executable).parent
            )
        except Exception as error:
            QMessageBox.information(self, tr("Обновление"), str(error))
            return
        dialog = QMessageBox(
            QMessageBox.Question,
            tr("Обновить приложение?"),
            tr("Скачать и установить версию ")
            + self.update_info["latest"]
            + tr("? Приложение перезапустится. Модели и настройки сохранятся."),
            QMessageBox.Yes | QMessageBox.No,
            self,
        )
        dialog.setDetailedText(self.update_info.get("notes", ""))
        if dialog.exec() != QMessageBox.Yes:
            return
        self.stop()
        self.update_open.setEnabled(False)
        cache = data_dir() / "updates"
        from update_ui import UpdateProgress

        self.update_cancel = threading.Event()
        self.update_dialog = UpdateProgress(self)
        self.update_dialog.cancel_requested.connect(self.update_cancel.set)
        self.update_dialog.show()

        def prepare(progress):
            unpacked = download(
                self.update_info,
                "Datastore24Kirill/OxyTranslateGame",
                "translator",
                cache,
                progress,
                self.update_cancel,
            )
            progress({"stage": "stage"})
            if self.update_cancel.is_set():
                raise InterruptedError(tr("Обновление отменено"))
            candidate = stage_replacement(unpacked, target, "translator")
            if self.update_cancel.is_set():
                import shutil

                shutil.rmtree(candidate.parent, ignore_errors=True)
                raise InterruptedError(tr("Обновление отменено"))
            return candidate

        self.install_job = Job(0, prepare)
        self.install_job.signals.progress.connect(
            lambda token, message: self.update_dialog.update_progress(message)
        )

        def prepared(token, candidate, error):
            if error:
                self.update_dialog.finish()
                self.install_job = None
                self.update_open.setEnabled(True)
                if self.update_cancel.is_set():
                    self.set_status(tr("Обновление отменено"))
                    return
                QMessageBox.warning(
                    self,
                    tr("Обновление не установлено"),
                    error + tr("\nТекущая версия сохранена."),
                )
                return

            def install_when_idle():
                if self.update_cancel.is_set():
                    import shutil

                    shutil.rmtree(candidate.parent, ignore_errors=True)
                    self.update_dialog.finish()
                    self.install_job = None
                    self.update_open.setEnabled(True)
                    return
                if self.active:
                    self.update_dialog.update_progress({"stage": "wait"})
                    self.set_status(
                        tr("Обновление готово. Ожидаю завершения текущей операции…")
                    )
                    QTimer.singleShot(500, install_when_idle)
                    return
                try:
                    self.update_dialog.update_progress({"stage": "install"})
                    launch_swap(candidate, target, cache, "OxyTranslateGame.exe")
                except Exception as failure:
                    self.update_dialog.finish()
                    self.install_job = None
                    self.update_open.setEnabled(True)
                    QMessageBox.warning(self, tr("Обновление"), str(failure))
                    return
                self.quit()

            install_when_idle()

        self.install_job.signals.done.connect(prepared)
        QThreadPool.globalInstance().start(self.install_job)

    def skip_update(self):
        if self.update_info:
            self.preferences.setValue("updates/skipped", self.update_info["latest"])
        self.update_notice.hide()
        self.update_open.hide()
        self.update_skip.hide()
        self.update_later.hide()

    def defer_update(self):
        self.update_later_until = time.monotonic() + 6 * 60 * 60
        self.update_notice.hide()
        self.update_open.hide()
        self.update_skip.hide()
        self.update_later.hide()

    def page(self, eyebrow, title, subtitle):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(32, 28, 32, 24)
        layout.setSpacing(17)
        layout.addWidget(label(eyebrow, "Eyebrow"))
        layout.addWidget(label(title, "Title"))
        layout.addWidget(label(subtitle, "Muted"))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(widget)
        self.pages.addWidget(scroll)
        return layout

    def build_translate(self):
        layout = self.page(
            tr("ПЕРЕВОД БЕЗ ГРАНИЦ"),
            tr("Перевод игры"),
            tr(
                "Выдели диалог — перевод появится рядом. Без скриншотов и текста в облаке."
            ),
        )
        box, panel = card()
        row = QHBoxLayout()
        row.addWidget(label("LOCAL TRANSLATION"))
        row.addStretch()
        row.addWidget(
            label("⌥⌘T" if sys.platform == "darwin" else "Ctrl + Alt + T", "Eyebrow")
        )
        panel.addLayout(row)
        actions = QHBoxLayout()
        self.select_btn = button(tr("＋  Выбрать область"), self.select_region, True)
        actions.addWidget(self.select_btn)
        self.again = button(tr("Перевести снова"), lambda: self.capture(True))
        actions.addWidget(self.again)
        actions.addWidget(button(tr("Стоп"), self.stop))
        panel.addLayout(actions)
        row = QHBoxLayout()
        self.watch = QCheckBox(tr("Автоматически следить за репликами"))
        self.watch.toggled.connect(self.watch_changed)
        row.addWidget(self.watch)
        row.addStretch()
        panel.addLayout(row)
        self.region_label = label(tr("Область пока не выбрана"), "Muted")
        panel.addWidget(self.region_label)
        layout.addWidget(box)
        box, panel = card()
        self.status = label(tr("Готов. Выбери область экрана."))
        panel.addWidget(self.status)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.hide()
        panel.addWidget(self.progress)
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText(
            tr(
                "Здесь появится перевод. Отдельное окно можно перемещать и менять его размер."
            )
        )
        self.preview.setMinimumHeight(110)
        panel.addWidget(self.preview)
        layout.addWidget(box, 1)
        row = QHBoxLayout()
        row.addWidget(button("Google ↗", lambda: self.open_online("google")))
        row.addWidget(button(tr("Яндекс ↗"), lambda: self.open_online("yandex")))
        row.addStretch()
        row.addWidget(label(tr("Онлайн — только по нажатию"), "Muted"))
        layout.addLayout(row)

    def build_settings(self):
        layout = self.page(
            tr("ПОД ВАШУ ИГРУ"),
            tr("Настройки"),
            tr("Оформление, перевод, доступ к экрану и обновления."),
        )
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        groups = QVBoxLayout(content)
        groups.setContentsMargins(0, 0, 8, 0)
        groups.setSpacing(16)
        scroll.setWidget(content)
        layout.addWidget(scroll)
        box, panel = card()
        panel.addWidget(label(tr("Оформление"), "Brand"))
        self.theme = QComboBox()
        for title, value in [
            (tr("Системная (авто)"), "system"),
            (tr("Светлая"), "light"),
            (tr("Тёмная"), "dark"),
        ]:
            self.theme.addItem(title, value)
        self.theme.setCurrentIndex(
            max(
                0,
                self.theme.findData(
                    self.preferences.value("appearance/theme", "system")
                ),
            )
        )
        self.theme.currentIndexChanged.connect(self.apply_theme)
        panel.addWidget(self.theme)
        panel.addWidget(
            label(tr("Тема применяется ко всем окнам и сохраняется сразу."), "Muted")
        )
        groups.addWidget(box)
        box, panel = card()
        panel.addWidget(label(tr("Перевод"), "Brand"))
        self.mode = QComboBox()
        self.mode.addItems(
            [
                tr("Быстрый · локальная модель Argos"),
                tr("Литературный · локальная модель Ollama"),
                tr("Ближе к оригиналу · Ollama"),
            ]
        )
        self.mode.setCurrentIndex(
            max(0, min(2, self.preferences.value("translation/mode", 0, type=int)))
        )
        self.mode.currentIndexChanged.connect(self.mode_changed)
        self.mode.currentIndexChanged.connect(
            lambda n: self.preferences.setValue("translation/mode", n)
        )
        panel.addWidget(self.mode)
        row = QHBoxLayout()
        row.addWidget(label(tr("Интервал автоматического перевода")))
        self.period = QSpinBox()
        self.period.setRange(1, 10)
        self.period.setValue(self.preferences.value("translation/period", 2, type=int))
        self.period.setSuffix(tr(" с"))
        self.period.valueChanged.connect(
            lambda n: (
                self.timer.setInterval(
                    max(
                        n,
                        5
                        if getattr(self, "economy", None) and self.economy.isChecked()
                        else 1,
                    )
                    * 1000
                ),
                self.preferences.setValue("translation/period", n),
            )
        )
        row.addWidget(self.period)
        panel.addLayout(row)
        groups.addWidget(box)
        box, panel = card()
        panel.addWidget(label(tr("Доступ к экрану"), "Brand"))
        self.permission_status = label("", "Muted")
        panel.addWidget(self.permission_status)
        self.permission_help = label(
            tr(
                "Нажмите «Разрешить запись экрана» и подтвердите запрос macOS. После выдачи доступа может потребоваться перезапуск."
            ),
            "Muted",
        )
        panel.addWidget(self.permission_help)
        row = QHBoxLayout()
        self.permission_button = button(
            tr("Настроить доступ"), self.permission_action, True
        )
        row.addWidget(self.permission_button)
        panel.addLayout(row)
        self.permission_feedback = label("", "Muted")
        self.permission_feedback.hide()
        panel.addWidget(self.permission_feedback)
        self.permission_details_toggle = button(
            tr("Доступ включён, но не работает ▸"), self.toggle_permission_details
        )
        panel.addWidget(self.permission_details_toggle)
        self.permission_details = QWidget()
        details = QVBoxLayout(self.permission_details)
        details.setContentsMargins(0, 0, 0, 0)
        details.addWidget(
            label(
                tr(
                    "Если после обновления флажок включён, а доступ не подтверждается, сохранённое разрешение может относиться к прежней подписи. Кнопка ниже удалит эту привязку, перезапустит приложение и вызовет новый запрос macOS."
                ),
                "Muted",
            )
        )
        self.permission_check = button(
            tr("Проверить доступ"), self.check_permission_now
        )
        details.addWidget(self.permission_check)
        details.addWidget(
            button(tr("Открыть настройки macOS ↗"), self.open_screen_settings)
        )
        self.permission_repair = button(
            tr("Сбросить старое разрешение…"), self.repair_permission
        )
        details.addWidget(self.permission_repair)
        panel.addWidget(self.permission_details)
        self.permission_details.hide()
        if sys.platform != "darwin":
            self.permission_button.hide()
            self.permission_details_toggle.hide()
        self.refresh_permission()
        groups.addWidget(box)
        box, panel = card()
        panel.addWidget(label(tr("Обновления"), "Brand"))
        self.auto_updates = QCheckBox(tr("Автоматически проверять новые версии"))
        self.auto_updates.setChecked(
            self.preferences.value("updates/auto", True, type=bool)
        )
        self.auto_updates.toggled.connect(
            lambda value: self.preferences.setValue("updates/auto", value)
        )
        panel.addWidget(self.auto_updates)
        panel.addWidget(
            button(tr("Проверить обновления"), lambda: self.check_updates(True))
        )
        panel.addWidget(label(tr("Версия ") + VERSION, "Muted"))
        groups.addWidget(box)
        groups.addStretch()

    def apply_theme(self, *_):
        value = self.theme.currentData()
        self.preferences.setValue("appearance/theme", value)
        app = QApplication.instance()
        dark = value == "dark" or (
            value == "system" and app.styleHints().colorScheme() == Qt.ColorScheme.Dark
        )
        app.setStyleSheet(
            stylesheet(dark)
            + (
                "\nQWidget { font-size: "
                + str(round(14 * self.ui_scale.value() / 100))
                + "px; }"
                if hasattr(self, "ui_scale")
                else ""
            )
        )
        palette = QPalette()
        for role, color in [
            (QPalette.Window, "#10151f" if dark else "#f3f6fb"),
            (QPalette.WindowText, "#e8edf7" if dark else "#172438"),
            (QPalette.Base, "#121b29" if dark else "#ffffff"),
            (QPalette.Text, "#e8edf7" if dark else "#172438"),
            (QPalette.ButtonText, "#e8edf7" if dark else "#172438"),
            (QPalette.Highlight, "#31594f" if dark else "#cceee3"),
            (QPalette.HighlightedText, "#ffffff" if dark else "#172438"),
        ]:
            palette.setColor(role, QColor(color))
        app.setPalette(palette)

    def permission_needs_repair(self, granted=None):
        previous = self.preferences.value("screen/lastGrantedVersion", "")
        return (
            sys.platform == "darwin"
            and bool(previous)
            and previous != VERSION
            and self.preferences.value("screen/repairedVersion", "") != VERSION
            and not (screen_access.allowed() if granted is None else granted)
        )

    def refresh_permission(self):
        try:
            granted = screen_access.allowed()
        except Exception:
            self.permission_status.setText(
                tr(
                    "Не удалось проверить разрешение macOS. Повторите проверку или откройте системные настройки."
                )
            )
            return False
        self.permission_status.setText(
            (
                tr("Разрешение macOS подтверждено. Можно выбрать область.")
                if sys.platform == "darwin"
                else tr("Отдельное разрешение macOS на Windows не требуется.")
            )
            if granted
            else tr("Доступ этой копии приложения пока не подтверждён.")
        )
        self.permission_help.setVisible(not granted and sys.platform == "darwin")
        self.permission_button.setVisible(True)
        self.permission_button.setText(
            tr("Выбрать область")
            if granted
            else tr("Перезапустить приложение")
            if self.permission_requested
            else tr("Разрешить запись экрана")
        )
        if self.permission_needs_repair(granted):
            self.permission_button.setText(tr("Восстановить доступ после обновления"))
            self.permission_status.setText(
                tr(
                    "macOS сохранила доступ для прежней версии. Восстановление перезапустит приложение и вызовет новый системный запрос."
                )
            )
        self.permission_details_toggle.setVisible(
            not granted and sys.platform == "darwin"
        )
        if granted:
            self.permission_details.hide()
            self.preferences.setValue("screen/lastGrantedVersion", VERSION)
        return granted

    def check_permission_now(self):
        granted = self.refresh_permission()
        stamp = time.strftime("%H:%M:%S")
        message = (
            (
                tr("Разрешение подтверждено. Нажмите «Перевод → Выбрать область».")
                if sys.platform == "darwin"
                else tr(
                    "Проверка разрешения macOS не нужна. Проверить захват можно через «Перевод → Выбрать область»."
                )
            )
            if granted
            else tr(
                "Разрешение не подтверждено. После выдачи доступа перезапустите приложение. Если после обновления это не помогло, используйте восстановление ниже."
            )
        )
        self.permission_feedback.setText(tr("Проверено в ") + stamp + ". " + message)
        self.permission_feedback.show()
        if not granted:
            self.permission_details.show()
            self.permission_details_toggle.setText(tr("Скрыть дополнительные шаги ▾"))

    def toggle_permission_details(self):
        visible = not self.permission_details.isVisible()
        self.permission_details.setVisible(visible)
        self.permission_details_toggle.setText(
            tr("Скрыть дополнительные шаги ▾")
            if visible
            else tr("Доступ включён, но не работает ▸")
        )

    def permission_action(self):
        if self.refresh_permission():
            self.select_region()
        elif self.permission_requested:
            self.restart_app()
        else:
            self.request_permission()

    def open_screen_settings(self):
        QDesktopServices.openUrl(
            QUrl(
                "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture"
            )
        )

    def request_permission(self):
        if self.active:
            self.set_status(
                tr("Дождитесь завершения текущей операции перед перезапуском.")
            )
            return
        if self.permission_needs_repair():
            try:
                screen_access.reset_current_app()
            except Exception as error:
                self.permission_feedback.setText(
                    tr("Не удалось восстановить доступ: ") + str(error)
                )
                self.permission_feedback.show()
                return
            self.preferences.setValue("screen/repairedVersion", VERSION)
            self.preferences.setValue("screen/requestAfterRestart", True)
            self.preferences.sync()
            self.restart_app()
            return
        if self.permission_requested:
            self.open_screen_settings()
            return
        self.permission_requested = True
        try:
            granted = screen_access.request()
        except Exception as error:
            self.permission_requested = False
            self.permission_feedback.setText(
                tr("Не удалось запросить доступ: ") + str(error)
            )
            self.permission_feedback.show()
            return
        self.refresh_permission()
        self.permission_feedback.setText(
            tr("Разрешение получено. Можно выбрать область.")
            if granted
            else tr(
                "Запрос отправлен macOS для этой копии приложения. Подтвердите разрешение в системном окне. Если macOS требует перезапуск, нажмите «Перезапустить приложение»."
            )
        )
        self.permission_feedback.show()
        if not granted:
            self.open_screen_settings()

    def repair_permission(self):
        if (
            QMessageBox.question(
                self,
                tr("Восстановить доступ?"),
                tr(
                    "Будет сброшено только разрешение записи экрана OxyTranslateGame. macOS попросит выдать его заново. Настройки и модели сохранятся. Продолжить?"
                ),
            )
            != QMessageBox.Yes
        ):
            return
        try:
            screen_access.reset_current_app()
        except Exception as error:
            QMessageBox.warning(
                self,
                tr("Восстановление доступа"),
                tr(
                    "Не удалось сбросить разрешение. Удалите OxyTranslateGame из списка записи экрана и добавьте снова.\n"
                )
                + str(error),
            )
            return
        self.preferences.setValue("screen/repairedVersion", VERSION)
        self.preferences.setValue("screen/requestAfterRestart", True)
        self.preferences.sync()
        self.restart_app()

    def restart_app(self):
        if self.active:
            self.set_status(
                tr("Дождитесь завершения текущей операции перед перезапуском.")
            )
            return
        try:
            if sys.platform == "darwin" and getattr(sys, "frozen", False):
                target = mac_bundle(sys.executable)
                subprocess.Popen(
                    [
                        "/bin/sh",
                        "-c",
                        'while kill -0 "$1" 2>/dev/null; do sleep 0.2; done; /usr/bin/open "$2"',
                        "restart",
                        str(os.getpid()),
                        str(target),
                    ],
                    start_new_session=True,
                )
            else:
                subprocess.Popen(
                    [sys.executable]
                    + (
                        []
                        if getattr(sys, "frozen", False)
                        else [str(Path(__file__).resolve())]
                    ),
                    start_new_session=True,
                )
        except Exception as error:
            QMessageBox.warning(self, tr("Перезапуск"), str(error))
            return
        self.quit()

    def build_models(self):
        layout = self.page(
            tr("ДВИЖКИ ПЕРЕВОДА"),
            tr("Два способа читать игру"),
            tr(
                "Первичная загрузка моделей требует интернета. Сам перевод — на твоём компьютере."
            ),
        )
        box, panel = card()
        panel.addWidget(label(tr("Быстрый перевод"), "Brand"))
        panel.addWidget(label("Argos / CTranslate2 · CPU", "Muted"))
        panel.addWidget(
            label(
                tr(
                    "Компактная офлайн-модель. Подходит для меню и коротких реплик. Имена иногда переводит буквально."
                )
            )
        )
        self.download = button(tr("Скачать офлайн-модель"), self.install_fast, True)
        panel.addWidget(self.download)
        layout.addWidget(box)
        box, panel = card()
        panel.addWidget(label(tr("Литературный перевод"), "Brand"))
        panel.addWidget(
            label(tr("Ollama · контекст трёх реплик · словарь имён"), "Muted")
        )
        panel.addWidget(
            label(
                tr(
                    "Более естественная речь и согласованные имена. Нужны Ollama и несколько гигабайт для модели. Скорость и качество зависят от компьютера."
                )
            )
        )
        self.model = QComboBox()
        self.model.addItems(["qwen3:4b", "qwen3:8b"])
        panel.addWidget(self.model)
        row = QHBoxLayout()
        row.addWidget(
            button(
                tr("Установить Ollama ↗"),
                lambda: QDesktopServices.openUrl(QUrl("https://ollama.com/download")),
            )
        )
        row.addWidget(button(tr("Скачать выбранную модель"), self.install_literary))
        panel.addLayout(row)
        layout.addWidget(box)
        self.model_status = label(
            tr("Модели не требуют API-ключа или подписки."), "Muted"
        )
        layout.addWidget(self.model_status)
        layout.addStretch()
        if self.engine.model_path():
            self.download.setText(tr("Офлайн-модель установлена ✓"))

    def build_glossary(self):
        layout = self.page(
            tr("ПОСЛЕДОВАТЕЛЬНОСТЬ"),
            tr("Имена остаются именами"),
            tr(
                "Словарь применяется в литературном режиме. Одна пара на строку: оригинал = перевод."
            ),
        )
        self.glossary = QPlainTextEdit()
        self.glossary.setPlaceholderText(
            "Mrs. Smith = миссис Смит\nRachel = Рэйчел\nLiza = Лиза"
        )
        layout.addWidget(self.glossary, 1)
        path = data_dir() / "glossary.txt"
        if path.exists():
            self.glossary.setPlainText(path.read_text(encoding="utf-8"))
        layout.addWidget(
            button(tr("Сохранить словарь на этом компьютере"), self.save_glossary, True)
        )

    def build_history(self):
        layout = self.page(
            tr("ТЕКУЩАЯ СЕССИЯ"),
            tr("Нить разговора"),
            tr("История локальна. Сохранение на диск включается отдельно."),
        )
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        layout.addWidget(self.history_text, 1)
        layout.addWidget(button(tr("Очистить историю и контекст"), self.clear_history))

    def open_page(self, index):
        self.pages.setCurrentIndex(index)
        for n, item in enumerate(self.nav_buttons):
            item.setChecked(n == index)

    def show_main(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def show_settings(self):
        self.open_page(4)
        self.show_main()

    def save_glossary(self):
        self.stop()
        (data_dir() / "glossary.txt").write_text(
            self.glossary.toPlainText(), encoding="utf-8"
        )
        self.set_status(tr("Словарь сохранён"))
        self.last = ""

    def clear_history(self):
        self.history.clear()
        self.context.clear()
        self.history_text.clear()
        self.last = ""
        if hasattr(self, "persist_history"):
            self.write_history()

    def mode_changed(self):
        if hasattr(self, "region_state"):
            self.region_state.clear()
        self.stop()
        self.last = ""

    def set_status(self, text):
        self.status.setText(tr(text))
        self.reader.status.setText(tr(text))
        if hasattr(self, "model_status"):
            self.model_status.setText(tr(text))

    def watch_changed(self, checked):
        if checked and self.region:
            self.timer.start(
                max(self.period.value(), 5 if self.economy.isChecked() else 1) * 1000
            )
            self.capture(False)
        elif checked:
            self.watch.setChecked(False)
            self.set_status(tr("Сначала выберите область."))
        else:
            self.timer.stop()

    def stop(self):
        self.token += 1
        self.cancel.set()
        self.capture_pending = False
        self.timer.stop()
        self.watch.setChecked(False)
        self.progress.hide()
        self.set_status(
            tr("Остановлено")
            if not self.active
            else tr("Отмена… ожидаю завершения текущей операции")
        )

    def closeEvent(self, event):
        self.stop()
        self.reader.hide()
        self.hide()
        event.ignore()

    def quit(self):
        self.stop()
        self.hotkey.close()
        QApplication.quit()

    def select_region(self):
        if self.active:
            self.set_status(
                tr("Дождитесь завершения текущей операции или нажмите «Стоп».")
            )
            return
        if not self.refresh_permission():
            self.show_settings()
            self.set_status(
                tr("Запрашиваю доступ к экрану для текущей копии приложения…")
            )
            if not self.permission_requested:
                self.request_permission()
            return
        self.stop()
        self.reader.hide()
        self.hide()
        for screen in QApplication.screens():
            selector = Selector(screen)
            selector.selected.connect(self.selected)
            selector.cancelled.connect(self.cancel_selection)
            self.selectors.append(selector)
            selector.show()
            selector.raise_()
        if self.selectors:
            self.selectors[0].activateWindow()

    def close_selectors(self):
        for selector in self.selectors:
            selector.close()
            selector.deleteLater()
        self.selectors.clear()

    def cancel_selection(self):
        self.close_selectors()
        self.show_main()
        self.set_status(tr("Выделение отменено"))

    def selected(self, screen, area):
        if not self.remember_region(screen, area):
            self.close_selectors()
            self.show_main()
            return
        self.region = (screen, QRect(area))
        self.last = ""
        self.reader_placed = False
        self.close_selectors()
        self.region_label.setText(f"{area.width()} × {area.height()} · {screen.name()}")
        QTimer.singleShot(200, lambda: self.capture(True))

    def launch_job(self, function, kind="translate"):
        if self.active:
            return
        self.cancel = threading.Event()
        token = self.token
        job = Job(token, function)
        self.active = job
        self.progress.show()
        job.signals.progress.connect(
            lambda t, msg: self.set_status(msg) if t == self.token else None
        )
        job.signals.recognized.connect(self.recognized)
        job.signals.done.connect(
            lambda t, value, error: self.finished(t, value, error, kind)
        )
        self.pool.start(job)

    def recognized(self, token, text):
        if token == self.token:
            self.current_original = text
            self.reader.original.setPlainText(text)

    def install_fast(self):
        source, target = self.pair()
        if source == "auto":
            self.set_status(tr("Для загрузки выберите исходный язык вручную."))
            return
        self.launch_job(
            lambda progress: self.engine.install(progress, self.cancel, source, target),
            "install",
        )

    def install_literary(self):
        model = self.model.currentText()
        self.launch_job(
            lambda progress: self.engine.pull_literary(model, progress, self.cancel),
            "install",
        )

    def capture(self, force):
        if self.active or self.capture_pending:
            return
        if not self.region:
            self.select_region()
            return
        try:
            if not self.track_window():
                self.advance_region()
                return
        except Exception:
            self.set_status(tr(tr("Не удалось проверить окно игры")))
            return
        self.capture_pending = True
        self.reader.hide()
        was_visible = self.isVisible()
        if was_visible:
            self.hide()
        token = self.token

        def grab():
            self.capture_pending = False
            if token != self.token:
                return
            try:
                screen, rect = self.region
                if screen not in QApplication.screens():
                    raise RuntimeError(tr("Экран отключён. Выберите область снова."))
                pix = screen.grabWindow(
                    0, rect.x(), rect.y(), rect.width(), rect.height()
                )
                if pix.isNull():
                    raise RuntimeError(
                        tr(
                            "Не удалось снять область. Проверьте доступ к записи экрана."
                        )
                    )
                image = pix.toImage().convertToFormat(QImage.Format_RGBA8888)
                self.last_capture = image.copy()
                import numpy as np

                rgba = (
                    np.frombuffer(image.bits(), dtype=np.uint8)
                    .reshape(image.height(), image.bytesPerLine())[
                        :, : image.width() * 4
                    ]
                    .reshape(image.height(), image.width(), 4)
                    .copy()
                )
                bgr = rgba[:, :, :3][:, :, ::-1].copy()
            except Exception as error:
                self.set_status(str(error))
                self.show_settings()
                self.timer.stop()
                self.watch.setChecked(False)
                return
            self.set_status(tr("Читаю текст…"))
            self.show_reader()
            source, target = self.pair()
            enhance = self.enhance.isChecked()
            contrast = self.contrast.isChecked()
            mode = self.mode.currentIndex()
            history = list(self.context)
            glossary = parse_glossary(self.glossary.toPlainText())
            model = self.model.currentText()
            previous = self.last

            def work(progress):
                started = time.monotonic()
                frame = bgr
                if enhance and frame.shape[0] < 300:
                    import cv2

                    frame = cv2.resize(
                        frame, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC
                    )
                if contrast:
                    import cv2

                    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
                    lab[:, :, 0] = cv2.createCLAHE(
                        clipLimit=2.0, tileGridSize=(8, 8)
                    ).apply(lab[:, :, 0])
                    frame = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
                text = self.engine.read(frame, source)
                ocr_seconds = time.monotonic() - started
                if token != self.token:
                    return None
                if not force:
                    if normalize(text) != self.stable_text:
                        self.stable_text = normalize(text)
                        return None
                if not normalize(text):
                    if not force:
                        return None
                    raise RuntimeError(
                        tr(
                            "Текст не найден. Выделите диалог крупнее и дождитесь окончания анимации."
                        )
                    )
                resolved = detect_source(text) if source == "auto" else source
                if not force and normalize(text) == previous:
                    return None
                if token != self.token:
                    return None
                self.active.signals.recognized.emit(token, text)
                progress(tr("Перевожу на компьютере…"))
                answer = (
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
                    )
                )
                self.last_metrics = {
                    "ocr_seconds": round(ocr_seconds, 3),
                    "total_seconds": round(time.monotonic() - started, 3),
                    "source": resolved,
                    "target": target,
                }
                return (text, answer)

            self.launch_job(work)

        QTimer.singleShot(140, grab)

    def show_reader(self):
        if not self.reader_placed and self.region:
            screen, area = self.region
            frame = screen.availableGeometry()
            p = screen.geometry().topLeft() + area.bottomLeft()
            x = min(max(p.x(), frame.left()), frame.right() - self.reader.width())
            y = min(max(p.y() + 16, frame.top()), frame.bottom() - self.reader.height())
            self.reader.move(x, y)
            self.reader_placed = True
        self.reader.show()

    def finished(self, token, value, error, kind):
        self.active = None
        self.progress.hide()
        if token != self.token:
            self.set_status(tr("Остановлено"))
            return
        if error:
            self.last_failure = kind + "Error"
            self.set_status(error)
            self.timer.stop()
            self.watch.setChecked(False)
            if kind == "translate":
                self.show_reader()
            return
        if kind == "catalog":
            self.catalog_items, ollama = value
            self.populate_catalog(ollama)
            return
        if kind == "remove_model":
            self.refresh_local_model()
            self.set_status(tr("Модель удалена"))
            return
        if kind == "install":
            self.set_status(tr("Модель готова. Можно переводить."))
            self.refresh_local_model()
            return
        if value is None:
            self.set_status(tr("Слежение: реплика не изменилась"))
            self.advance_region()
            return
        original, translated = value
        self.context.append((original, translated))
        self.last = normalize(original)
        self.current_original = original
        if self.keep_history.isChecked():
            self.history.append((original, translated))
        self.render_history()
        self.write_history()
        self.metrics_label.setText(
            f"OCR {self.last_metrics.get('ocr_seconds', 0):.2f}s · Total {self.last_metrics.get('total_seconds', 0):.2f}s"
        )
        self.preview.setPlainText(translated)
        self.reader.text.setPlainText(translated)
        self.reader.original.setPlainText(original)
        self.set_status(tr("Перевод готов · локально"))
        self.show_reader()
        self.advance_region()

    def open_online(self, provider):
        if not self.current_original:
            self.set_status(tr("Сначала выделите и распознайте текст."))
            return
        title = "Google" if provider == "google" else tr("Яндекс")
        choice = QMessageBox.question(
            self,
            tr("Открыть онлайн-переводчик?"),
            tr(
                "Распознанный текст будет передан сервису {0} через браузер. Снимок экрана не отправляется. Продолжить?"
            ).format(title),
        )
        if choice != QMessageBox.Yes:
            return
        if provider == "google":
            url = "https://translate.google.com/?" + urlencode(
                {
                    "sl": self.source.currentData(),
                    "tl": self.target.currentData(),
                    "text": self.current_original,
                    "op": "translate",
                }
            )
        else:
            url = "https://translate.yandex.ru/?" + urlencode(
                {
                    "source_lang": self.source.currentData(),
                    "target_lang": self.target.currentData(),
                    "text": self.current_original,
                }
            )
        QDesktopServices.openUrl(QUrl(url))


def main():
    if "--self-test" in sys.argv:
        try:
            import numpy as np
            from PIL import Image, ImageDraw, ImageFont

            image = Image.new("RGB", (600, 100), "white")
            ImageDraw.Draw(image).text(
                (20, 20),
                "Talk to Rachel",
                fill="black",
                font=ImageFont.load_default(size=34),
            )
            text = LocalEngines().read(np.asarray(image)[:, :, ::-1].copy())
            if (
                detect_source(
                    "This is a conversation about a village and the people who live there."
                )
                != "en"
            ):
                raise RuntimeError("Bundled language detection failed")
            if "Rachel" not in text:
                raise RuntimeError("Bundled OCR did not recognize fixture")
            if sys.stdout:
                print("SELF_TEST_OK: bundled OCR recognized fixture", flush=True)
            return 0
        except Exception as error:
            if sys.stderr:
                print(str(error), file=sys.stderr)
            return 1
    app = QApplication(sys.argv)
    app.setApplicationName("OxyTranslateGame")
    app.setOrganizationName("OxyFire")
    app.setQuitOnLastWindowClosed(False)
    app.setStyle("Fusion")
    window = Main()
    window.show()
    app.aboutToQuit.connect(window.hotkey.close)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
