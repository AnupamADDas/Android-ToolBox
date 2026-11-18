; Reproducible, per-user Windows installer. Build with python build_installer.py.
#ifndef AppVersion
  #define AppVersion "1.2.0"
#endif
#ifndef AppSource
  #define AppSource "..\dist\windows\Android_Toolbox"
#endif
#ifndef OutputPath
  #define OutputPath "..\dist\installer"
#endif

[Setup]
AppId={{D5A79D01-3F24-4D7E-9AE6-ABA95387B7C1}
AppName=Android Toolbox
AppVersion={#AppVersion}
AppVerName=Android Toolbox {#AppVersion}
VersionInfoVersion={#AppVersion}
VersionInfoDescription=Android Toolbox Setup
DefaultDirName={localappdata}\Programs\Android Toolbox
DefaultGroupName=Android Toolbox
DisableProgramGroupPage=yes
AllowNoIcons=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir={#OutputPath}
OutputBaseFilename=Android-Toolbox-Setup-{#AppVersion}-x64
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\Android_Toolbox.exe
UninstallDisplayName=Android Toolbox
WizardStyle=modern dark
WizardSmallImageFile=..\assets\installer-header.bmp
WizardSmallImageBackColor=$2C1C10
DisableWelcomePage=no
Compression=lzma2
SolidCompression=yes
CloseApplications=yes
CloseApplicationsFilter=Android_Toolbox.exe
RestartApplications=no
SetupLogging=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: unchecked

[Files]
Source: "{#AppSource}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Android Toolbox"; Filename: "{app}\Android_Toolbox.exe"; WorkingDir: "{app}"; IconFilename: "{app}\Android_Toolbox.exe"; AppUserModelID: "AndroidToolbox.Desktop"
Name: "{autodesktop}\Android Toolbox"; Filename: "{app}\Android_Toolbox.exe"; WorkingDir: "{app}"; IconFilename: "{app}\Android_Toolbox.exe"; AppUserModelID: "AndroidToolbox.Desktop"; Tasks: desktopicon

[Run]
Filename: "{app}\Android_Toolbox.exe"; Description: "Launch Android Toolbox"; Flags: nowait postinstall skipifsilent
