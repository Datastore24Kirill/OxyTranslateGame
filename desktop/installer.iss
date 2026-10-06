#define AppVersion "0.3.1"
[Setup]
AppId={{CB12CE82-09C5-42F8-A628-BE2E0685D47F}
AppName=OxyTranslateGame
AppVersion={#AppVersion}
AppPublisher=OxyTranslateGame contributors
AppPublisherURL=https://github.com/Datastore24Kirill/OxyTranslateGame
DefaultDirName={localappdata}\Programs\OxyTranslateGame
DefaultGroupName=OxyTranslateGame
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist\desktop
OutputBaseFilename=OxyTranslateGame-0.3.1-Windows-x64-Setup
SetupIconFile=AppIcon.ico
UninstallDisplayIcon={app}\OxyTranslateGame.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
LicenseFile=..\LICENSE
[Files]
Source: "..\dist\desktop\OxyTranslateGame\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\OxyTranslateGame"; Filename: "{app}\OxyTranslateGame.exe"
Name: "{autodesktop}\OxyTranslateGame"; Filename: "{app}\OxyTranslateGame.exe"; Tasks: desktopicon
[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked
[Run]
Filename: "{app}\OxyTranslateGame.exe"; Description: "Launch OxyTranslateGame"; Flags: nowait postinstall skipifsilent
