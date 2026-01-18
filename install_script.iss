; Script Installer ROG Music Player + Auto VLC
; Dibuat Khusus untuk Rafi

[Setup]
; Informasi Aplikasi
AppName=ROG Music Player
AppVersion=1.0
AppPublisher=Rafi Engineer
AppPublisherURL=https://github.com/rafiproject
AppSupportURL=https://github.com/rafiproject
AppUpdatesURL=https://github.com/rafiproject

; Lokasi Install Default (Program Files)
DefaultDirName={autopf}\ROG Music Player
DefaultGroupName=ROG Music Player

; Nama File Installer Hasil Akhir
OutputBaseFilename=ROG_Music_Player_Setup_v1
Compression=lzma
SolidCompression=yes

; Supaya terlihat modern di Windows 10/11
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; 1. FILE UTAMA APLIKASI (Pastikan Path ini BENAR sesuai folder komputer kamu)
Source: "D:\02 DATA\04 Rafi\Project\musicPlayer\dist\ROG_Music_Player.exe"; DestDir: "{app}"; Flags: ignoreversion

; 2. FILE PENDUKUNG (Folder Assets - Jika ada gambar/icon)
; Source: "D:\02 DATA\04 Rafi\Project\musicPlayer\assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

; 3. INSTALLER VLC (Untuk instalasi otomatis)
Source: "D:\02 DATA\04 Rafi\Project\musicPlayer\vlc_installer.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{group}\ROG Music Player"; Filename: "{app}\ROG_Music_Player.exe"
Name: "{autodesktop}\ROG Music Player"; Filename: "{app}\ROG_Music_Player.exe"; Tasks: desktopicon

[Run]
; Jalankan aplikasi setelah selesai install
Filename: "{app}\ROG_Music_Player.exe"; Description: "{cm:LaunchProgram,ROG Music Player}"; Flags: nowait postinstall skipifsilent

[Code]
// --- LOGIKA CERDAS: CEK & INSTALL VLC OTOMATIS ---

function IsVLCInstalled: Boolean;
begin
  // Mengecek Registry Windows apakah VLC sudah ada
  Result := RegKeyExists(HKLM, 'SOFTWARE\VideoLAN\VLC') or 
            RegKeyExists(HKLM64, 'SOFTWARE\VideoLAN\VLC');
end;

procedure InitializeWizard;
var
  ResultCode: Integer;
begin
  // Jika VLC TIDAK ditemukan...
  if not IsVLCInstalled then
  begin
    // Tampilkan pesan peringatan ke user
    if MsgBox('Aplikasi ROG Music Player membutuhkan VLC Media Player agar suara bisa berjalan lancar.' + #13#10 + #13#10 +
              'Sistem mendeteksi VLC belum terinstall di komputer ini.' + #13#10 +
              'Apakah Anda ingin menginstal VLC sekarang secara otomatis?', mbConfirmation, MB_YESNO) = IDYES then
    begin
      // Ekstrak installer VLC ke folder sementara (Temp)
      ExtractTemporaryFile('vlc_installer.exe');
      
      // Jalankan installer VLC secara "Silent" (Tanpa ribet klik Next)
      // /L=1033 artinya bahasa Inggris, /S artinya Silent Install
      if not Exec(ExpandConstant('{tmp}\vlc_installer.exe'), '/L=1033 /S', '', SW_SHOW, ewWaitUntilTerminated, ResultCode) then
      begin
        MsgBox('Gagal menginstal VLC otomatis. Silakan instal manual nanti.', mbError, MB_OK);
      end;
    end;
  end;
end;