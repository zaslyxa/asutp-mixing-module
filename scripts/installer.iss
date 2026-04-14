#define AppName "ASUTP Mixing Module"
#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif
#define AppPublisher "ASUTP Team"
#define AppExeName "asutp-mixing-module.exe"

[Setup]
AppId={{2B30D9D9-CC06-46FD-A93F-3A38FB98258D}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\ASUTP Mixing Module
DefaultGroupName=ASUTP Mixing Module
UninstallDisplayIcon={app}\{#AppExeName}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=dist
OutputBaseFilename=asutp-mixing-module-setup

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "config\*"; DestDir: "{app}\config"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "docs\*"; DestDir: "{app}\docs"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\ASUTP Mixing Module"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\ASUTP Mixing Module"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch ASUTP Mixing Module"; Flags: nowait postinstall skipifsilent
