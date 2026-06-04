#define MyAppName "SimpleScope PC"
#define MyAppPublisher "SimpleOscilloscope"
#define MyAppExeName "SimpleScopePC.exe"
#ifndef MyAppVersion
#define MyAppVersion "0.9.2"
#endif

[Setup]
AppId={{9C62C6A1-8F0B-4C17-9D5A-5F3A6E2E1001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\SimpleScope PC
DefaultGroupName=SimpleScope PC
OutputDir=..\..\dist\installer
OutputBaseFilename=SimpleScopePC-{#MyAppVersion}-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=..\assets\SimpleScopePC.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务："; Flags: unchecked

[Files]
Source: "..\..\dist\SimpleScopePC\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\SimpleScope PC"; Filename: "{app}\{#MyAppExeName}"
Name: "{commondesktop}\SimpleScope PC"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 SimpleScope PC"; Flags: nowait postinstall skipifsilent
