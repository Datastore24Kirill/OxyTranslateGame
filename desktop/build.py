"""Create a downloadable app bundle / Windows portable directory. No runtime Python required."""
import os
import platform
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
IS_MAC = sys.platform == 'darwin'
icon = ROOT / ('Resources/AppIcon.icns' if IS_MAC else 'desktop/AppIcon.ico')
command = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--windowed',
    '--name', 'OxyTranslateGame', '--distpath', 'dist/desktop', '--workpath', 'build/desktop',
    '--specpath', 'build', '--icon', str(icon), '--paths', str(ROOT/'desktop'),
    '--add-data', str(ROOT/'desktop/AppIcon.png') + os.pathsep + '.',
    '--add-data', str(ROOT/'desktop/THIRD_PARTY.md') + os.pathsep + '.',
    '--add-data', str(ROOT/'LICENSE') + os.pathsep + '.',
    '--collect-all', 'rapidocr_onnxruntime', '--collect-all', 'ctranslate2',
    '--collect-all', 'onnxruntime', '--collect-all', 'sentencepiece', '--collect-data', 'certifi',
    '--copy-metadata', 'PySide6_Essentials', '--copy-metadata', 'shiboken6',
    '--exclude-module', 'PySide6.QtWebEngineCore', '--exclude-module', 'PySide6.QtWebEngineWidgets',
    '--exclude-module', 'PySide6.QtQml', '--exclude-module', 'PySide6.QtQuick',
    str(ROOT/'desktop/app.py')]
if IS_MAC: command += ['--osx-bundle-identifier', 'com.oxyfire.OxyTranslateGame.Desktop']
subprocess.run(command, check=True)
output = ROOT/'dist/desktop'
if IS_MAC:
    import plistlib
    bundle = output/'OxyTranslateGame.app'
    info = bundle/'Contents/Info.plist'
    data = plistlib.loads(info.read_bytes())
    data.update(CFBundleShortVersionString='0.2.4', CFBundleVersion='6', LSMinimumSystemVersion='14.0',
                NSScreenCaptureUsageDescription='Read only the screen area you select for local translation.')
    info.write_bytes(plistlib.dumps(data))
    subprocess.run(['codesign','--force','--deep','--sign',os.environ.get('CODESIGN_IDENTITY','-'),str(bundle)],check=True)
    subprocess.run(['codesign','--verify','--deep','--strict',str(bundle)],check=True)
    archive = output/f'OxyTranslateGame-0.2.4-macOS-{platform.machine()}.zip'
    subprocess.run(['ditto','-c','-k','--sequesterRsrc','--keepParent',str(bundle),str(archive)],check=True)
else:
    shutil.make_archive(str(output/'OxyTranslateGame-0.2.4-Windows-x64-Portable'),'zip',str(output),'OxyTranslateGame')
print('BUILD_OK', flush=True)
