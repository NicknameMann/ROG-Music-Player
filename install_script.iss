; Script Installer ROG Music Player v1.1
; Edisi: Settings & Persistent Data

[Setup]
; --- INFO APLIKASI ---
AppName=ROG Music Player
AppVersion=1.1
AppPublisher=Rafi Engineer
AppPublisherURL=https://github.com/rafiproject
DefaultDirName={autopf}\ROG Music Player
DefaultGroupName=ROG Music Player

; --- OUTPUT FILE ---
; Nama file installer nanti: ROG_Music_Player_Setup_v1.1.exe
OutputBaseFilename=ROG_Music_Player_Setup_v1.1
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; 1. FILE EXE UTAMA (Pastikan path ini benar)
Source: "D:\02 DATA\04 Rafi\Project\musicPlayer\dist\ROG_Music_Player.exe"; DestDir: "{app}"; Flags: ignoreversion

; 2. INSTALLER VLC (Wajib ada di folder project musicPlayer)
Source: "D:\02 DATA\04 Rafi\Project\musicPlayer\vlc_installer.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{group}\ROG Music Player"; Filename: "{app}\ROG_Music_Player.exe"
Name: "{autodesktop}\ROG Music Player"; Filename: "{app}\ROG_Music_Player.exe"; Tasks: desktopicon

[Run]
; Jalankan aplikasi setelah selesai install
Filename: "{app}\ROG_Music_Player.exe"; Description: "{cm:LaunchProgram,ROG Music Player}"; Flags: nowait postinstall skipifsilent

[Code]
// --- LOGIKA CEK VLC ---
function IsVLCInstalled: Boolean;
begin
  Result := RegKeyExists(HKLM, 'SOFTWARE\VideoLAN\VLC') or 
            RegKeyExists(HKLM64, 'SOFTWARE\VideoLAN\VLC');
end;

procedure InitializeWizard;
var
  ResultCode: Integer;
begin
  if not IsVLCInstalled then
  begin
    if MsgBox('ROG Music Player v1.1 membutuhkan VLC Media Player.' + #13#10 +
              'VLC tidak ditemukan.' + #13#10 + #13#10 +
              'Install VLC otomatis sekarang?', mbConfirmation, MB_YESNO) = IDYES then
    begin
      ExtractTemporaryFile('vlc_installer.exe');
      if not Exec(ExpandConstant('{tmp}\vlc_installer.exe'), '/L=1033 /S', '', SW_SHOW, ewWaitUntilTerminated, ResultCode) then
      begin
        MsgBox('Gagal install VLC. Mohon install manual.', mbError, MB_OK);
      end;
    end;
  end;
end;