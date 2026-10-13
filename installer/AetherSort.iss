#define AppName "AetherSort"
#define AppVersion "0.3.0-beta.1"
#define AppPublisher "AetherSort"
#define AppExeName "AetherSort.exe"

[Setup]
AppId={{D7E4B9A4-4F2B-49CF-8B11-71A3A4A8B031}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\AetherSort
DefaultGroupName=AetherSort
DisableProgramGroupPage=yes
OutputDir=..\dist\installer
OutputBaseFilename=AetherSort-Setup-{#AppVersion}-x64
SetupIconFile=..\aethersort\assets\aethersort.ico
UninstallDisplayIcon={app}\AetherSort.exe
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
WizardStyle=modern
Compression=lzma2
SolidCompression=yes
CloseApplications=yes
RestartApplications=no
; Unsigned beta: Windows SmartScreen may display a warning until the publisher signs releases.

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\AetherSort\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\AetherSort"; Filename: "{app}\AetherSort.exe"
Name: "{autodesktop}\AetherSort"; Filename: "{app}\AetherSort.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\AetherSort.exe"; Description: "Launch AetherSort"; Flags: postinstall nowait skipifsilent
