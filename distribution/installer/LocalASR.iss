; One stable per-user product identity. Never change AppId for an upgrade.
#ifndef AppVersion
  #error AppVersion must come from src/app_version.py via build_installer.ps1
#endif
#ifndef PayloadDir
  #error PayloadDir is required
#endif
#ifndef ProjectRoot
  #error ProjectRoot is required
#endif
#ifndef ArtifactDir
  #error ArtifactDir is required
#endif
[Setup]
AppId={{013B05DD-FB78-45E4-8C99-1256B77D01F2}
AppName=LocalASR
AppVersion={#AppVersion}
AppPublisher=LocalASR Project
AppPublisherURL=https://github.com/769399481/LocalASR
AppSupportURL=https://github.com/769399481/LocalASR/issues
AppUpdatesURL=https://github.com/769399481/LocalASR/releases
AppVerName=LocalASR {#AppVersion}
VersionInfoDescription=LocalASR Setup
VersionInfoProductName=LocalASR
DefaultDirName={localappdata}\Programs\LocalASR
DefaultGroupName=LocalASR
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
LicenseFile={#ProjectRoot}\LICENSE
OutputDir={#ArtifactDir}
OutputBaseFilename=LocalASR-Setup-{#AppVersion}-win64
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
DisableWelcomePage=no
UninstallDisplayName=LocalASR
UninstallDisplayIcon={app}\LocalASR.exe
CloseApplications=yes
CloseApplicationsFilter=*.exe,*.dll,*.pyd
RestartApplications=no
SetupLogging=yes
; No signed flag without a real certificate.
[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"; Flags: unchecked
[Files]
Source: "{#PayloadDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#ProjectRoot}\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#ProjectRoot}\COMMERCIAL_LICENSE.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#ProjectRoot}\PRIVACY.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#ProjectRoot}\SECURITY.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#ProjectRoot}\THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{group}\LocalASR"; Filename: "{app}\LocalASR.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\LocalASR"; Filename: "{app}\LocalASR.exe"; WorkingDir: "{app}"; Tasks: desktopicon
[Run]
Filename: "{app}\LocalASR.exe"; Description: "Launch LocalASR"; Flags: nowait postinstall skipifsilent
; Deliberately no UninstallDelete / InstallDelete: user files are never erased.
[Code]
function AppIsRunning(): Boolean;
var Locator, Service, Processes: Variant;
begin
  { Fail closed if WMI is unavailable; never force-kill an app or risk unsaved work. }
  Result := True;
  try
    Locator := CreateOleObject('WbemScripting.SWbemLocator');
    Service := Locator.ConnectServer('', 'root\CIMV2');
    Processes := Service.ExecQuery('SELECT ProcessId FROM Win32_Process WHERE Name = ''LocalASR.exe''');
    Result := Processes.Count > 0;
  except
    Log('Unable to check running LocalASR processes. Stop for safety.');
  end;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  if AppIsRunning() then
    Result := 'Please close LocalASR, then retry. Your models and user data will be preserved.';
end;

function InitializeUninstall(): Boolean;
begin
  Result := not AppIsRunning();
  if not Result then
    MsgBox('Please close LocalASR before uninstalling. Models, settings and exports will be preserved.', mbInformation, MB_OK);
end;
