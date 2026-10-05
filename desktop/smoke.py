import subprocess
import sys
from pathlib import Path
root = Path(__file__).resolve().parents[1] / 'dist/desktop'
exe = root/'OxyTranslateGame.app/Contents/MacOS/OxyTranslateGame' if sys.platform == 'darwin' else root/'OxyTranslateGame/OxyTranslateGame.exe'
subprocess.run([str(exe), '--self-test'], check=True, timeout=90)
print('Packaged OCR smoke test passed')
