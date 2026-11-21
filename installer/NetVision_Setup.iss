; NetVision - Inno Setup Script
; Builds a professional, non-elevated per-user Windows Installer

#define MyAppName "NetVision"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "BTech CSE Academic Projects"
#define MyAppURL "https://github.com/netvision/netvision"
#define MyAppExeName "NetVision.exe"

[Setup]
AppId={{5E28B0D3-78DF-4B52-97EA-541249A2B991}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Per-user installation (does not require UAC administrator rights)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\installer
OutputBaseFilename=NetVision_Setup_Inno
SetupIconFile=..\assets\icons\netvision.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\NetVision\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up app files without deleting user measurements in %LOCALAPPDATA%\NetVision
Type: filesandordirs; Name: "{app}"
