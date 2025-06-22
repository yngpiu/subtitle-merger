; Inno Setup Script for Subtitle Merger

[Setup]
AppName=Subtitle Merger
AppVersion=1.0
AppPublisher=Your Name
DefaultDirName={autopf}\Subtitle Merger
DefaultGroupName=Subtitle Merger

; --- THAY ĐỔI QUAN TRỌNG NHẤT ---
; Yêu cầu chạy với quyền Admin để có thể ghi vào Program Files
PrivilegesRequired=admin

OutputBaseFilename=Subtitle_Merger_Setup_v1.0
SetupIconFile=E:\Projects\NMIXX\PythonProject\logo.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "E:\Projects\NMIXX\PythonProject\dist\app.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Subtitle Merger"; Filename: "{app}\app.exe"
; Dòng này giờ sẽ hoạt động bình thường vì đã có quyền Admin
Name: "{commondesktop}\Subtitle Merger"; Filename: "{app}\app.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
