STYLE = '''
QWidget { background: #10151f; color: #e8edf7; font-family: "Segoe UI", "SF Pro Display", "Arial"; font-size: 14px; }
QMainWindow { background: #10151f; }
QLabel { background: transparent; }
QLabel#Brand { font-size: 25px; font-weight: 700; }
QLabel#Title { font-size: 30px; font-weight: 700; }
QLabel#Muted { color: #94a3ba; }
QLabel#Eyebrow { color: #70dfc3; font-size: 11px; font-weight: 700; }
QFrame#Sidebar { background: #0c111a; border-right: 1px solid #243044; }
QFrame#Card, QGroupBox { background: #182131; border: 1px solid #2b394f; border-radius: 16px; }
QFrame#Card QLabel { background: transparent; }
QPushButton { background: #253248; border: 1px solid #34465f; border-radius: 9px; padding: 11px 16px; font-weight: 600; }
QPushButton:hover { background: #34465f; }
QPushButton:pressed { background: #1e293b; }
QPushButton:disabled { color: #66758b; background: #192231; border-color: #243044; }
QPushButton#Primary { background: #66e0bd; color: #092f2a; border: none; }
QPushButton#Primary:hover { background: #93efd3; }
QPushButton#Nav { background: transparent; border: 0; text-align: left; color: #9cacbf; }
QPushButton#Nav:checked { background: #1e3b3a; color: #83e8c9; }
QComboBox, QLineEdit, QSpinBox { background: #121b29; border: 1px solid #35465e; border-radius: 8px; padding: 9px; }
QComboBox::drop-down { border: 0; width: 26px; }
QComboBox QAbstractItemView { background: #192536; selection-background-color: #31594f; padding: 8px; }
QTextEdit, QPlainTextEdit { background: #121b29; border: 1px solid #2b394f; border-radius: 10px; padding: 12px; selection-background-color: #296958; }
QCheckBox { spacing: 10px; background: transparent; }
QCheckBox::indicator { width: 18px; height: 18px; border: 1px solid #50617a; border-radius: 5px; background: #182131; }
QCheckBox::indicator:checked { background: #66e0bd; border-color: #66e0bd; }
QProgressBar { background: #182131; border-radius: 4px; border: 0; height: 5px; }
QProgressBar::chunk { background: #66e0bd; border-radius: 4px; }
QSlider::groove:horizontal { height: 4px; background: #33445c; border-radius: 2px; }
QSlider::handle:horizontal { background: #66e0bd; width: 14px; margin: -5px 0; border-radius: 7px; }
QScrollBar:vertical { width: 7px; background: transparent; }
QScrollBar::handle:vertical { background: #41516b; border-radius: 3px; min-height: 20px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
'''

# Apply one complete palette to the main window, reader, menus and form controls.
LIGHT = {
    '#10151f': '#f3f6fb', '#e8edf7': '#172438', '#94a3ba': '#526379',
    '#70dfc3': '#08745c', '#0c111a': '#e8eef6', '#243044': '#d1dbe8',
    '#182131': '#ffffff', '#2b394f': '#cbd7e5', '#253248': '#e2eaf4',
    '#34465f': '#c5d4e6', '#1e293b': '#d4e0ef', '#66758b': '#64748b',
    '#192231': '#e7edf5', '#66e0bd': '#66e0bd', '#9cacbf': '#485c74',
    '#1e3b3a': '#cceee3', '#83e8c9': '#075b47', '#121b29': '#ffffff',
    '#35465e': '#bfcede', '#192536': '#ffffff', '#31594f': '#cceee3',
    '#296958': '#b7e4d6', '#50617a': '#889bb2', '#33445c': '#bccbdb',
    '#41516b': '#97aac1',
}

def stylesheet(dark=True):
    import re
    style = STYLE if dark else re.sub(r'#[0-9a-f]{6}', lambda m: LIGHT.get(m[0], m[0]), STYLE)
    return style + '\nQMenu { padding: 6px; } QMenu::item { padding: 8px 18px; } QMenu::item:selected { background: ' + ('#31594f' if dark else '#cceee3') + '; } QScrollArea { border: none; }'
