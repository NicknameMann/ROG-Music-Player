; Script Installer ROG Music Player v1.5 (Final Perfected)
; Fitur: Pilih Lokasi Install + Auto Uninstall Lama + Cek VLC

[Setup]
; --- INFO APLIKASI ---
; Jangan ubah AppId ini agar fitur update/uninstall berjalan lancar
AppId={{A1B2C3D4-E5F6-9012-3456-7890ABCDEF12}
AppName=ROG Music Player
AppVersion=1.3
AppPublisher=Baraendra Rafi
AppPublisherURL=https://github.com/rafiproject

; --- PENGATURAN FOLDER INSTALASI (YANG KAMU MINTA) ---
; {autopf} artinya otomatis ke Program Files.
DefaultDirName={autopf}\ROG Music Player
DefaultGroupName=ROG Music Player

; --- MEMUNCULKAN HALAMAN PILIH LOKASI ---
; "no" artinya JANGAN matikan halaman ini (alias: TAMPILKAN)
DisableDirPage=no
DisableProgramGroupPage=no

; --- OUTPUT FILE ---
OutputBaseFilename=ROG_Music_Player_Setup_v1.3_Fixed
Compression=lzma
SolidCompression=yes
WizardStyle=modern

; --- IZIN ADMIN (Wajib untuk install di Program Files & Install VLC) ---
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; 1. FILE EXE UTAMA
Source: "D:\02 DATA\04 Rafi\Project\musicPlayer\dist\ROG_Music_Player.exe"; DestDir: "{app}"; Flags: ignoreversion

; 2. FILE PENDUKUNG
Source: "D:\02 DATA\04 Rafi\Project\musicPlayer\ffmpeg.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "D:\02 DATA\04 Rafi\Project\musicPlayer\assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

; 3. INSTALLER VLC
Source: "D:\02 DATA\04 Rafi\Project\musicPlayer\vlc_installer.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{group}\ROG Music Player"; Filename: "{app}\ROG_Music_Player.exe"
Name: "{autodesktop}\ROG Music Player"; Filename: "{app}\ROG_Music_Player.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\ROG_Music_Player.exe"; Description: "{cm:LaunchProgram,ROG Music Player}"; Flags: nowait postinstall skipifsilent

[Code]
// --- FUNGSI 1: CEK & UNINSTALL VERSI LAMA ---
procedure RemoveOldVersion();
var
  sUnInstallString: String;
  iResultCode: Integer;
begin
  // Cek registry untuk mencari uninstaller versi sebelumnya (berdasarkan AppId)
  if RegQueryStringValue(HKLM, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{{A1B2C3D4-E5F6-9012-3456-7890ABCDEF12}_is1', 'UninstallString', sUnInstallString) then
  begin
    // Hapus tanda kutip jika ada
    StringChange(sUnInstallString, '"', '');
    
    // Jalankan Uninstaller versi lama secara SILENT (User tidak perlu klik yes/next lagi)
    Exec(sUnInstallString, '/SILENT /NORESTART /SUPPRESSMSGBOXES', '', SW_HIDE, ewWaitUntilTerminated, iResultCode);
  end;
end;

// --- FUNGSI 2: CEK VLC PLAYER ---
function IsVLCInstalled: Boolean;
begin
  Result := RegKeyExists(HKLM, 'SOFTWARE\VideoLAN\VLC') or 
            RegKeyExists(HKLM64, 'SOFTWARE\VideoLAN\VLC');
end;

// --- FUNGSI UTAMA ---
procedure InitializeWizard;
var
  ResultCode: Integer;
begin
  // 1. Bersihkan versi lama dulu (Clean Install)
  RemoveOldVersion();

  // 2. Cek apakah VLC sudah ada
  if not IsVLCInstalled then
  begin
    if MsgBox('Aplikasi ini membutuhkan VLC Media Player.' + #13#10 +
              'VLC tidak ditemukan di komputer ini.' + #13#10 + #13#10 +
              'Install VLC otomatis sekarang?', mbConfirmation, MB_YESNO) = IDYES then
    begin
      try
        ExtractTemporaryFile('vlc_installer.exe');
        // Coba install silent
        if Exec(ExpandConstant('{tmp}\vlc_installer.exe'), '/L=1033 /S', '', SW_SHOW, ewWaitUntilTerminated, ResultCode) then
        begin
           if ResultCode <> 0 then
           begin
             MsgBox('Gagal auto-install VLC. Browser akan dibuka.', mbError, MB_OK);
             ShellExec('open', 'https://www.videolan.org/vlc/', '', '', SW_SHOW, ewNoWait, ResultCode);
           end;
        end
        else
        begin
           MsgBox('Installer VLC error. Download manual.', mbError, MB_OK);
           ShellExec('open', 'https://www.videolan.org/vlc/', '', '', SW_SHOW, ewNoWait, ResultCode);
        end;
      except
        MsgBox('File VLC Installer tidak ditemukan. Download manual.', mbInformation, MB_OK);
        ShellExec('open', 'https://www.videolan.org/vlc/', '', '', SW_SHOW, ewNoWait, ResultCode);
      end;
    end;
  end;
end;