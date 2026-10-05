import ctypes
import json
import os
import sys
import threading
import time
from collections import deque
from pathlib import Path
from urllib.parse import urlencode

from PySide6.QtCore import Qt, QRect, Signal, QObject, QRunnable, QThreadPool, QTimer, QUrl, QSettings
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QKeySequence, QShortcut, QDesktopServices, QIcon, QImage
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QStackedWidget, QComboBox, QTextEdit, QPlainTextEdit, QCheckBox,
    QSlider, QSpinBox, QMessageBox, QProgressBar, QSystemTrayIcon, QMenu)
from engines import LocalEngines, data_dir, normalize, parse_glossary
from platform_hotkey import Hotkey
from theme import STYLE
from releases import check_release
from updater import download, mac_bundle, stage_replacement, launch_swap

VERSION = '0.2.3'


class Signals(QObject):
    done = Signal(int, object, str)
    progress = Signal(int, str)
    recognized = Signal(int, str)


class Job(QRunnable):
    def __init__(self, token, function):
        super().__init__(); self.token = token; self.function = function; self.signals = Signals()
    def run(self):
        try: self.signals.done.emit(self.token, self.function(lambda text: self.signals.progress.emit(self.token, text)), '')
        except Exception as error: self.signals.done.emit(self.token, None, str(error))


def button(text, action=None, primary=False):
    result = QPushButton(text)
    if primary: result.setObjectName('Primary')
    if action: result.clicked.connect(action)
    return result


def label(text, style=None):
    widget = QLabel(text); widget.setWordWrap(True)
    if style: widget.setObjectName(style)
    return widget


def card():
    frame = QFrame(); frame.setObjectName('Card'); layout = QVBoxLayout(frame)
    layout.setContentsMargins(22, 20, 22, 20); layout.setSpacing(12)
    return frame, layout


class Selector(QWidget):
    selected = Signal(object, object)
    cancelled = Signal()
    def __init__(self, screen):
        super().__init__(None, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.screen = screen; self.origin = None; self.area = QRect()
        self.setAttribute(Qt.WA_TranslucentBackground); self.setGeometry(screen.geometry())
        self.setCursor(Qt.CrossCursor); self.setMouseTracking(True)
    def paintEvent(self, event):
        painter = QPainter(self); painter.fillRect(self.rect(), QColor(5, 14, 26, 115))
        if not self.area.isNull():
            painter.setCompositionMode(QPainter.CompositionMode_Clear); painter.fillRect(self.area, Qt.transparent)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.setPen(QPen(QColor('#66e0bd'), 2)); painter.drawRect(self.area)
        painter.setPen(Qt.white); painter.setFont(QFont('Arial', 17))
        painter.drawText(28, 44, 'Выделите текст  •  Esc — отмена')
    def mousePressEvent(self, event): self.origin = event.position().toPoint()
    def mouseMoveEvent(self, event):
        if self.origin is not None:
            self.area = QRect(self.origin, event.position().toPoint()).normalized().intersected(self.rect()); self.update()
    def mouseReleaseEvent(self, event):
        self.mouseMoveEvent(event)
        if self.area.width() >= 20 and self.area.height() >= 20: self.selected.emit(self.screen, self.area)
        else: self.cancelled.emit()
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape: self.cancelled.emit()


class Reader(QWidget):
    closed = Signal()
    def __init__(self, owner):
        super().__init__(None, Qt.Tool | Qt.WindowStaysOnTopHint)
        self.owner = owner; self.setWindowTitle('OxyTranslateGame · Перевод'); self.resize(580, 330)
        self.setMinimumSize(390, 240)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        layout = QVBoxLayout(self); layout.setContentsMargins(20, 18, 20, 18); layout.setSpacing(12)
        head = QHBoxLayout(); head.addWidget(label('OXY / ПЕРЕВОД', 'Eyebrow')); head.addStretch()
        head.addWidget(button('Настройки', owner.show_settings)); head.addWidget(button('✕', self.close)); layout.addLayout(head)
        self.status = label('Готов к переводу', 'Muted'); layout.addWidget(self.status)
        self.text = QTextEdit(); self.text.setReadOnly(True); self.text.setStyleSheet('font-size: 21px; border: none; background: transparent;'); layout.addWidget(self.text, 1)
        self.original = QTextEdit(); self.original.setReadOnly(True); self.original.setMaximumHeight(120); self.original.hide(); layout.addWidget(self.original)
        row = QHBoxLayout(); self.original_toggle = QCheckBox('Оригинал'); self.original_toggle.toggled.connect(self.original.setVisible); row.addWidget(self.original_toggle)
        row.addWidget(button('Копировать', lambda: QApplication.clipboard().setText(self.text.toPlainText()))); row.addStretch()
        row.addWidget(label('A')); font = QSlider(Qt.Horizontal); font.setRange(15, 34); font.setValue(21); font.setMaximumWidth(95)
        font.valueChanged.connect(lambda size: self.text.setStyleSheet(f'font-size: {size}px; border: none; background: transparent;'))
        row.addWidget(font); layout.addLayout(row)
        opacity = QSlider(Qt.Horizontal); opacity.setRange(45, 100); opacity.setValue(100); opacity.setMaximumWidth(130); opacity.valueChanged.connect(lambda value: self.setWindowOpacity(value / 100))
        row2 = QHBoxLayout(); row2.addWidget(label('Непрозрачность', 'Muted')); row2.addWidget(opacity); row2.addStretch(); layout.addLayout(row2)
        QShortcut(QKeySequence('Escape'), self, activated=self.close)
    def closeEvent(self, event): self.closed.emit(); event.accept()


class Main(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle('OxyTranslateGame'); self.resize(1020, 780); self.setMinimumSize(880, 690)
        self.preferences = QSettings(); self.update_job = None; self.update_info = None; self.update_later_until = 0; self.permission_requested = False; self.install_job = None
        self.engine = LocalEngines(); self.pool = QThreadPool(); self.pool.setMaxThreadCount(1)
        self.token = 0; self.active = None; self.cancel = threading.Event(); self.region = None; self.selectors = []
        self.history = deque(maxlen=30); self.last = ''; self.current_original = ''; self.capture_pending = False; self.reader_placed = False
        self.reader = Reader(self); self.reader.closed.connect(self.stop)
        root = QWidget(); self.setCentralWidget(root); base = QHBoxLayout(root); base.setContentsMargins(0, 0, 0, 0); base.setSpacing(0)
        sidebar = QFrame(); sidebar.setObjectName('Sidebar'); sidebar.setFixedWidth(214); nav = QVBoxLayout(sidebar); nav.setContentsMargins(22, 30, 18, 25)
        icon_path = Path(getattr(sys, '_MEIPASS', Path(__file__).parent)) / 'AppIcon.png'
        brand_icon = QLabel(); brand_icon.setPixmap(QIcon(str(icon_path)).pixmap(76, 76)); brand_icon.setAccessibleName('Логотип OxyTranslateGame'); nav.addWidget(brand_icon)
        nav.addWidget(label('Oxy\nTranslateGame', 'Brand')); nav.addWidget(label('YOUR GAME. YOUR LANGUAGE.', 'Eyebrow')); nav.addSpacing(30)
        self.pages = QStackedWidget(); self.nav_buttons = []
        for index, title in enumerate(['Перевод', 'Модели', 'Имена и термины', 'История']):
            item = button(title, lambda checked=False, n=index: self.open_page(n)); item.setObjectName('Nav'); item.setCheckable(True); nav.addWidget(item); self.nav_buttons.append(item)
        nav.addStretch()
        self.update_notice = label('', 'Muted'); self.update_notice.hide(); nav.addWidget(self.update_notice)
        self.update_open = button('Обновить', self.open_update); self.update_open.hide(); nav.addWidget(self.update_open)
        self.update_skip = button('Пропустить версию', self.skip_update); self.update_skip.hide(); nav.addWidget(self.update_skip)
        self.update_later = button('Позже', self.defer_update); self.update_later.hide(); nav.addWidget(self.update_later)
        nav.addWidget(button('Проверить версию', lambda: self.check_updates(True)))
        self.auto_updates = QCheckBox('Автопроверка GitHub'); self.auto_updates.setChecked(self.preferences.value('updates/auto', True, type=bool)); self.auto_updates.toggled.connect(lambda value: self.preferences.setValue('updates/auto', value)); nav.addWidget(self.auto_updates)
        nav.addWidget(label('●  LOCAL FIRST', 'Eyebrow')); nav.addWidget(label('Mac + Windows\nv' + VERSION, 'Muted'))
        base.addWidget(sidebar); base.addWidget(self.pages, 1)
        self.build_translate(); self.build_models(); self.build_glossary(); self.build_history(); self.open_page(0)
        self.timer = QTimer(self); self.timer.timeout.connect(lambda: self.capture(False))
        self.hotkey = Hotkey(QApplication.instance()); self.hotkey.activated.connect(self.select_region)
        if not self.hotkey.ok: self.set_status('Горячая клавиша занята. Используйте кнопку выбора области.')
        self.tray = QSystemTrayIcon(self)
        icon_path = Path(getattr(sys, '_MEIPASS', Path(__file__).parent)) / 'AppIcon.png'
        if icon_path.exists():
            app_icon = QIcon(str(icon_path)); QApplication.instance().setWindowIcon(app_icon); self.setWindowIcon(app_icon); self.reader.setWindowIcon(app_icon); self.tray.setIcon(app_icon)
        menu = QMenu(); menu.addAction('Выбрать область', self.select_region); menu.addAction('Остановить', self.stop); menu.addAction('Открыть настройки', self.show_settings); menu.addAction('Выход', self.quit)
        menu.addAction('Проверить обновления', lambda: self.check_updates(True))
        self.tray.setContextMenu(menu); self.tray.show()
        self.update_timer = QTimer(self); self.update_timer.timeout.connect(self.check_updates); self.update_timer.start(6 * 60 * 60 * 1000)
        QTimer.singleShot(12000, self.check_updates)

    def check_updates(self, manual=False):
        if self.update_job or (not manual and (not self.auto_updates.isChecked() or time.monotonic() < self.update_later_until)): return
        self.update_job = Job(0, lambda progress: check_release('Datastore24Kirill/OxyTranslateGame', VERSION, allow_preview=True))
        self.update_job.signals.done.connect(lambda token, info, error: self.update_checked(info, error, manual))
        QThreadPool.globalInstance().start(self.update_job)

    def update_checked(self, info, error, manual):
        self.update_job = None
        if error:
            if manual: QMessageBox.information(self, 'Обновления', 'Не удалось проверить релизы. Проверьте подключение и повторите позже.')
            return
        if not info:
            if manual: QMessageBox.information(self, 'Обновления', 'Новых готовых сборок нет.')
            return
        if not manual and self.preferences.value('updates/skipped', '') == info['latest']: return
        self.update_info = info
        self.update_notice.setText('Доступна версия ' + info['latest'] + (' (предварительная)' if info['preview'] else ''))
        self.update_notice.show(); self.update_open.show(); self.update_skip.show(); self.update_later.show()

    def open_update(self):
        if not self.update_info or self.install_job: return
        try:
            if not getattr(sys, 'frozen', False): raise RuntimeError('Автообновление доступно в готовой сборке приложения.')
            target = mac_bundle(sys.executable) if sys.platform == 'darwin' else Path(sys.executable).parent
        except Exception as error:
            QMessageBox.information(self, 'Обновление', str(error)); return
        if QMessageBox.question(self, 'Обновить приложение?', 'Скачать и установить версию ' + self.update_info['latest'] + '? Приложение перезапустится. Модели и настройки сохранятся.') != QMessageBox.Yes: return
        self.stop(); self.update_open.setEnabled(False)
        cache = data_dir() / 'updates'
        def prepare(progress):
            unpacked = download(self.update_info, 'Datastore24Kirill/OxyTranslateGame', 'translator', cache, progress)
            return stage_replacement(unpacked, target, 'translator')
        self.install_job = Job(0, prepare)
        self.install_job.signals.progress.connect(lambda token, message: self.set_status(message))
        def prepared(token, candidate, error):
            if error:
                self.install_job = None; self.update_open.setEnabled(True)
                QMessageBox.warning(self, 'Обновление не установлено', error + '\nТекущая версия сохранена.'); return
            def install_when_idle():
                if self.active:
                    self.set_status('Обновление готово. Ожидаю завершения текущей операции…')
                    QTimer.singleShot(500, install_when_idle); return
                try: launch_swap(candidate, target, cache, 'OxyTranslateGame.exe')
                except Exception as failure:
                    self.install_job = None; self.update_open.setEnabled(True); QMessageBox.warning(self, 'Обновление', str(failure)); return
                self.quit()
            install_when_idle()
        self.install_job.signals.done.connect(prepared)
        QThreadPool.globalInstance().start(self.install_job)

    def skip_update(self):
        if self.update_info: self.preferences.setValue('updates/skipped', self.update_info['latest'])
        self.update_notice.hide(); self.update_open.hide(); self.update_skip.hide(); self.update_later.hide()

    def defer_update(self):
        self.update_later_until = time.monotonic() + 6 * 60 * 60
        self.update_notice.hide(); self.update_open.hide(); self.update_skip.hide(); self.update_later.hide()

    def page(self, eyebrow, title, subtitle):
        widget = QWidget(); layout = QVBoxLayout(widget); layout.setContentsMargins(32, 28, 32, 24); layout.setSpacing(17)
        layout.addWidget(label(eyebrow, 'Eyebrow')); layout.addWidget(label(title, 'Title')); layout.addWidget(label(subtitle, 'Muted'))
        self.pages.addWidget(widget); return layout

    def build_translate(self):
        layout = self.page('ПЕРЕВОД БЕЗ ГРАНИЦ', 'Понимай историю.\nОставайся в игре.', 'Выдели диалог — русский перевод появится рядом. Без скриншотов и текста в облаке.')
        box, panel = card(); row = QHBoxLayout(); row.addWidget(label('English  →  Русский')); row.addStretch(); row.addWidget(label('⌥⌘T' if sys.platform == 'darwin' else 'Ctrl + Alt + T', 'Eyebrow')); panel.addLayout(row)
        self.mode = QComboBox(); self.mode.addItems(['Быстрый · локальная модель Argos', 'Литературный · локальная модель Ollama']); self.mode.currentIndexChanged.connect(self.mode_changed); panel.addWidget(self.mode)
        actions = QHBoxLayout(); self.select_btn = button('＋  Выбрать область', self.select_region, True); actions.addWidget(self.select_btn)
        self.again = button('Перевести снова', lambda: self.capture(True)); actions.addWidget(self.again); actions.addWidget(button('Стоп', self.stop)); panel.addLayout(actions)
        row = QHBoxLayout(); self.watch = QCheckBox('Автоматически следить за репликами'); self.watch.toggled.connect(self.watch_changed); row.addWidget(self.watch); row.addStretch()
        self.period = QSpinBox(); self.period.setRange(1, 10); self.period.setValue(2); self.period.setSuffix(' с'); self.period.valueChanged.connect(lambda n: self.timer.setInterval(n * 1000)); row.addWidget(self.period); panel.addLayout(row)
        self.region_label = label('Область пока не выбрана', 'Muted'); panel.addWidget(self.region_label); layout.addWidget(box)
        box, panel = card(); self.status = label('Готов. Выбери область экрана.'); panel.addWidget(self.status)
        self.progress = QProgressBar(); self.progress.setRange(0, 0); self.progress.setTextVisible(False); self.progress.hide(); panel.addWidget(self.progress)
        self.preview = QTextEdit(); self.preview.setReadOnly(True); self.preview.setPlaceholderText('Здесь появится перевод. Отдельное окно можно перемещать и менять его размер.'); self.preview.setMinimumHeight(110); panel.addWidget(self.preview); layout.addWidget(box, 1)
        row = QHBoxLayout(); row.addWidget(button('Google ↗', lambda: self.open_online('google'))); row.addWidget(button('Яндекс ↗', lambda: self.open_online('yandex'))); row.addStretch(); row.addWidget(label('Онлайн — только по нажатию', 'Muted')); layout.addLayout(row)

    def build_models(self):
        layout = self.page('ДВИЖКИ ПЕРЕВОДА', 'Два способа читать игру', 'Первичная загрузка моделей требует интернета. Сам перевод — на твоём компьютере.')
        box, panel = card(); panel.addWidget(label('Быстрый перевод', 'Brand')); panel.addWidget(label('Argos / CTranslate2 · CPU · English → Русский', 'Muted'))
        panel.addWidget(label('Компактная офлайн-модель. Подходит для меню и коротких реплик. Имена иногда переводит буквально.'))
        self.download = button('Скачать офлайн-модель', self.install_fast, True); panel.addWidget(self.download); layout.addWidget(box)
        box, panel = card(); panel.addWidget(label('Литературный перевод', 'Brand')); panel.addWidget(label('Ollama · контекст трёх реплик · словарь имён', 'Muted'))
        panel.addWidget(label('Более естественная речь и согласованные имена. Нужны Ollama и несколько гигабайт для модели. Скорость и качество зависят от компьютера.'))
        self.model = QComboBox(); self.model.addItems(['qwen3:4b', 'qwen3:8b']); panel.addWidget(self.model)
        row = QHBoxLayout(); row.addWidget(button('Установить Ollama ↗', lambda: QDesktopServices.openUrl(QUrl('https://ollama.com/download')))); row.addWidget(button('Скачать выбранную модель', self.install_literary)); panel.addLayout(row); layout.addWidget(box)
        self.model_status = label('Модели не требуют API-ключа или подписки.', 'Muted'); layout.addWidget(self.model_status); layout.addStretch()
        if self.engine.model_path(): self.download.setText('Офлайн-модель установлена ✓')

    def build_glossary(self):
        layout = self.page('ПОСЛЕДОВАТЕЛЬНОСТЬ', 'Имена остаются именами', 'Словарь применяется в литературном режиме. Одна пара на строку: оригинал = перевод.')
        self.glossary = QPlainTextEdit(); self.glossary.setPlaceholderText('Mrs. Smith = миссис Смит\nRachel = Рэйчел\nLiza = Лиза'); layout.addWidget(self.glossary, 1)
        path = data_dir() / 'glossary.txt'
        if path.exists(): self.glossary.setPlainText(path.read_text(encoding='utf-8'))
        layout.addWidget(button('Сохранить словарь на этом компьютере', self.save_glossary, True))
        layout.addWidget(label('Сохраняется только этот словарь. История диалогов и снимки на диск не записываются.', 'Muted'))

    def build_history(self):
        layout = self.page('ТЕКУЩАЯ СЕССИЯ', 'Нить разговора', 'Последние 30 переводов. История очищается после выхода; ничего не отправляется в сеть.')
        self.history_text = QTextEdit(); self.history_text.setReadOnly(True); layout.addWidget(self.history_text, 1)
        layout.addWidget(button('Очистить историю и контекст', self.clear_history))

    def open_page(self, index):
        self.pages.setCurrentIndex(index)
        for n, item in enumerate(self.nav_buttons): item.setChecked(n == index)
    def show_settings(self): self.show(); self.raise_(); self.activateWindow()
    def save_glossary(self):
        (data_dir() / 'glossary.txt').write_text(self.glossary.toPlainText(), encoding='utf-8'); self.set_status('Словарь сохранён'); self.last = ''
    def clear_history(self): self.history.clear(); self.history_text.clear(); self.last = ''
    def mode_changed(self): self.stop(); self.last = ''
    def set_status(self, text):
        self.status.setText(text); self.reader.status.setText(text)
        if hasattr(self, 'model_status'): self.model_status.setText(text)
    def watch_changed(self, checked):
        if checked and self.region:
            self.timer.start(self.period.value() * 1000); self.capture(False)
        elif checked: self.watch.setChecked(False); self.set_status('Сначала выберите область.')
        else: self.timer.stop()
    def stop(self):
        self.token += 1; self.cancel.set(); self.capture_pending = False; self.timer.stop(); self.watch.setChecked(False)
        self.progress.hide(); self.set_status('Остановлено' if not self.active else 'Отмена… ожидаю завершения текущей операции')
    def closeEvent(self, event):
        self.stop(); self.reader.hide(); self.hide(); event.ignore()
    def quit(self): self.stop(); self.hotkey.close(); QApplication.quit()

    def select_region(self):
        if self.active: self.set_status('Дождитесь завершения текущей операции или нажмите «Стоп».'); return
        if sys.platform == 'darwin':
            cg = ctypes.CDLL('/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics')
            cg.CGPreflightScreenCaptureAccess.restype = ctypes.c_bool
            if not cg.CGPreflightScreenCaptureAccess():
                self.set_status('macOS не подтверждает разрешение записи экрана. После обновления может потребоваться повторное разрешение и перезапуск.')
                dialog = QMessageBox(self); dialog.setWindowTitle('Доступ к записи экрана'); dialog.setText('macOS не подтверждает доступ для этой копии приложения.')
                dialog.setInformativeText('Если переключатель уже включён: завершите приложение, удалите старую запись OxyTranslateGame в настройках записи экрана, добавьте используемую копию заново и перезапустите её. Временная подпись релиза может меняться при обновлении.\n\nЗапущенный файл: ' + sys.executable)
                request = dialog.addButton('Запросить доступ', QMessageBox.AcceptRole); request.setEnabled(not self.permission_requested)
                settings = dialog.addButton('Открыть настройки', QMessageBox.ActionRole)
                dialog.addButton('Отмена', QMessageBox.RejectRole); dialog.exec()
                if dialog.clickedButton() == settings:
                    QDesktopServices.openUrl(QUrl('x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture'))
                elif dialog.clickedButton() == request and not self.permission_requested:
                    self.permission_requested = True; cg.CGRequestScreenCaptureAccess.restype = ctypes.c_bool; cg.CGRequestScreenCaptureAccess()
                return
        self.stop(); self.reader.hide(); self.hide()
        for screen in QApplication.screens():
            selector = Selector(screen); selector.selected.connect(self.selected); selector.cancelled.connect(self.cancel_selection); self.selectors.append(selector); selector.show(); selector.raise_()
        if self.selectors: self.selectors[0].activateWindow()
    def close_selectors(self):
        for selector in self.selectors: selector.close(); selector.deleteLater()
        self.selectors.clear()
    def cancel_selection(self): self.close_selectors(); self.show_settings(); self.set_status('Выделение отменено')
    def selected(self, screen, area):
        self.region = (screen, QRect(area)); self.last = ''; self.reader_placed = False; self.close_selectors()
        self.region_label.setText(f'{area.width()} × {area.height()} · {screen.name()}')
        QTimer.singleShot(200, lambda: self.capture(True))

    def launch_job(self, function, kind='translate'):
        if self.active: return
        self.cancel = threading.Event(); token = self.token
        job = Job(token, function); self.active = job; self.progress.show()
        job.signals.progress.connect(lambda t, msg: self.set_status(msg) if t == self.token else None)
        job.signals.recognized.connect(self.recognized)
        job.signals.done.connect(lambda t, value, error: self.finished(t, value, error, kind))
        self.pool.start(job)

    def recognized(self, token, text):
        if token == self.token:
            self.current_original = text; self.reader.original.setPlainText(text)

    def install_fast(self):
        self.launch_job(lambda progress: self.engine.install(progress, self.cancel), 'install')
    def install_literary(self):
        model = self.model.currentText()
        self.launch_job(lambda progress: self.engine.pull_literary(model, progress, self.cancel), 'install')

    def capture(self, force):
        if self.active or self.capture_pending: return
        if not self.region: self.select_region(); return
        self.capture_pending = True; self.reader.hide(); was_visible = self.isVisible()
        if was_visible: self.hide()
        token = self.token
        def grab():
            self.capture_pending = False
            if token != self.token: return
            try:
                screen, rect = self.region
                if screen not in QApplication.screens(): raise RuntimeError('Экран отключён. Выберите область снова.')
                pix = screen.grabWindow(0, rect.x(), rect.y(), rect.width(), rect.height())
                if pix.isNull(): raise RuntimeError('Не удалось снять область. Проверьте доступ к записи экрана.')
                image = pix.toImage().convertToFormat(QImage.Format_RGBA8888)
                import numpy as np
                rgba = np.frombuffer(image.bits(), dtype=np.uint8).reshape(image.height(), image.bytesPerLine())[:, :image.width()*4].reshape(image.height(), image.width(), 4).copy()
                bgr = rgba[:, :, :3][:, :, ::-1].copy()
            except Exception as error:
                self.set_status(str(error)); self.show_settings(); self.timer.stop(); self.watch.setChecked(False); return
            self.set_status('Читаю текст…'); self.show_reader()
            mode = self.mode.currentIndex(); history = list(self.history); glossary = parse_glossary(self.glossary.toPlainText()); model = self.model.currentText(); previous = self.last
            def work(progress):
                text = self.engine.read(bgr)
                if not normalize(text): raise RuntimeError('Текст не найден. Выделите диалог крупнее и дождитесь окончания анимации.')
                if not force and normalize(text) == previous: return None
                if self.cancel.is_set(): return None
                self.active.signals.recognized.emit(token, text)
                progress('Перевожу на компьютере…')
                answer = self.engine.fast(text) if mode == 0 else self.engine.literary(text, history, glossary, model)
                return text, answer
            self.launch_job(work)
        QTimer.singleShot(140, grab)

    def show_reader(self):
        if not self.reader_placed and self.region:
            screen, area = self.region; frame = screen.availableGeometry(); p = screen.geometry().topLeft() + area.bottomLeft()
            x = min(max(p.x(), frame.left()), frame.right() - self.reader.width())
            y = min(max(p.y() + 16, frame.top()), frame.bottom() - self.reader.height())
            self.reader.move(x, y); self.reader_placed = True
        self.reader.show()

    def finished(self, token, value, error, kind):
        self.active = None; self.progress.hide()
        if token != self.token:
            self.set_status('Остановлено'); return
        if error:
            self.set_status(error); self.timer.stop(); self.watch.setChecked(False)
            if kind == 'translate': self.show_reader()
            return
        if kind == 'install':
            self.set_status('Модель готова. Можно переводить.'); self.download.setText('Офлайн-модель установлена ✓' if self.engine.model_path() else 'Скачать офлайн-модель'); return
        if value is None: self.set_status('Слежение: реплика не изменилась'); return
        original, translated = value; self.last = normalize(original); self.current_original = original
        self.history.append((original, translated)); self.preview.setPlainText(translated); self.reader.text.setPlainText(translated); self.reader.original.setPlainText(original)
        self.history_text.setPlainText('\n\n────────────\n\n'.join(a + '\n\n' + b for a, b in reversed(self.history)))
        self.set_status('Перевод готов · локально'); self.show_reader()

    def open_online(self, provider):
        if not self.current_original: self.set_status('Сначала выделите и распознайте текст.'); return
        title = 'Google' if provider == 'google' else 'Яндекс'
        choice = QMessageBox.question(self, 'Открыть онлайн-переводчик?', f'Распознанный текст будет передан сервису {title} через браузер. Снимок экрана не отправляется. Продолжить?')
        if choice != QMessageBox.Yes: return
        if provider == 'google': url = 'https://translate.google.com/?' + urlencode({'sl':'en', 'tl':'ru', 'text':self.current_original, 'op':'translate'})
        else: url = 'https://translate.yandex.ru/?' + urlencode({'source_lang':'en', 'target_lang':'ru', 'text':self.current_original})
        QDesktopServices.openUrl(QUrl(url))


def main():
    if '--self-test' in sys.argv:
        try:
            import numpy as np
            from PIL import Image, ImageDraw, ImageFont
            image = Image.new('RGB', (600, 100), 'white')
            ImageDraw.Draw(image).text((20, 20), 'Talk to Rachel', fill='black', font=ImageFont.load_default(size=34))
            text = LocalEngines().read(np.asarray(image)[:, :, ::-1].copy())
            if 'Rachel' not in text: raise RuntimeError('Bundled OCR did not recognize fixture')
            if sys.stdout: print('SELF_TEST_OK: bundled OCR recognized fixture', flush=True)
            return 0
        except Exception as error:
            if sys.stderr: print(str(error), file=sys.stderr)
            return 1
    app = QApplication(sys.argv); app.setApplicationName('OxyTranslateGame'); app.setOrganizationName('OxyFire'); app.setQuitOnLastWindowClosed(False); app.setStyleSheet(STYLE)
    window = Main(); window.show(); app.aboutToQuit.connect(window.hotkey.close)
    return app.exec()

if __name__ == '__main__': sys.exit(main())
