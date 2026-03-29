@echo off
title NEXUS Start v3.0 - Build
color 0B & cls
echo.
echo  ╔══════════════════════════════════════════════════════════════╗
echo  ║         NEXUS START MENU v3.0 — AUTO BUILD                  ║
echo  ║  Animasyonlar · Araçlar · Klasörler · Pano · Takvim · QR    ║
echo  ╚══════════════════════════════════════════════════════════════╝
echo.

:: ── Python kontrolü ────────────────────────────────────────────────────────
where python >nul 2>nul || (
    echo  [HATA] Python bulunamadi! python.org'dan yukleyin.
    start https://www.python.org/downloads/
    pause & exit /b 1
)
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYV=%%v
echo  [OK] Python %PYV%
echo.

:: ── Sanal ortam ────────────────────────────────────────────────────────────
set VENV=%~dp0venv
if not exist "%VENV%" (
    echo  [1/6] Sanal ortam olusturuluyor...
    python -m venv "%VENV%"
) else echo  [1/6] Sanal ortam mevcut.
echo.

call "%VENV%\Scripts\activate.bat"

:: ── Bağımlılıklar ──────────────────────────────────────────────────────────
echo  [2/6] Bagimliliklar yukleniyor...
pip install --upgrade pip -q
pip install -r "%~dp0requirements.txt" -q
if %errorlevel% neq 0 (
    echo  [HATA] Kurulum basarisiz! Detay icin tekrar calistirin:
    pip install -r "%~dp0requirements.txt"
    pause & exit /b 1
)
echo  [OK]
echo.

:: ── pywin32 post-install ───────────────────────────────────────────────────
echo  [3/6] pywin32 post-install...
python "%VENV%\Scripts\pywin32_postinstall.py" -install >nul 2>nul
echo  [OK]
echo.

:: ── EXE derleme ───────────────────────────────────────────────────────────
echo  [4/6] EXE derleniyor (2-5 dk surebilir)...
echo        Moduler yapi: 6 dosya tek EXE'ye ekleniyor...
set OUT=%~dp0dist

pip install pyinstaller -q

pyinstaller --noconfirm --windowed --onefile ^
    --name "NexusStart" ^
    --distpath "%OUT%" ^
    --workpath "%~dp0build_tmp" ^
    --specpath "%~dp0build_tmp" ^
    --add-data "%~dp0config.py;." ^
    --add-data "%~dp0animations.py;." ^
    --add-data "%~dp0threads.py;." ^
    --add-data "%~dp0widgets.py;." ^
    --add-data "%~dp0settings_panel.py;." ^
    --hidden-import "config" ^
    --hidden-import "animations" ^
    --hidden-import "threads" ^
    --hidden-import "widgets" ^
    --hidden-import "settings_panel" ^
    --hidden-import "win32com.client" ^
    --hidden-import "win32api" ^
    --hidden-import "win32con" ^
    --hidden-import "win32gui" ^
    --hidden-import "winshell" ^
    --hidden-import "psutil" ^
    --hidden-import "PIL" ^
    --hidden-import "qrcode" ^
    --hidden-import "qrcode.image.pil" ^
    --hidden-import "urllib.request" ^
    --hidden-import "urllib.parse" ^
    --hidden-import "calendar" ^
    --hidden-import "math" ^
    --hidden-import "string" ^
    --collect-all "PyQt6" ^
    --collect-all "win32com" ^
    "%~dp0main.py"

if %errorlevel% neq 0 (
    echo  [HATA] Derleme basarisiz! Yukaridaki hata mesajina bak.
    pause & exit /b 1
)
echo  [OK]
echo.

:: ── Klasörler ve kısayol ──────────────────────────────────────────────────
echo  [5/6] Klasorler ve kisayol hazirlaniyor...
set SC=%APPDATA%\NexusStart\shortcuts
if not exist "%SC%" mkdir "%SC%"
(
echo Bu klasore .lnk kisayol dosyasi atin.
echo Uygulama NEXUS Start menusunde otomatik gozukur.
) > "%SC%\README.txt"

powershell -NoProfile -Command ^
  "$ws=New-Object -ComObject WScript.Shell;" ^
  "$s=$ws.CreateShortcut([Environment]::GetFolderPath('Desktop')+'\NexusStart Shortcuts.lnk');" ^
  "$s.TargetPath='%SC:\=\\%';" ^
  "$s.Save()" >nul 2>nul
echo  [OK]
echo.

:: ── Masaüstüne NexusStart kısayolu ────────────────────────────────────────
echo  [6/6] Masaustu kisayolu olusturuluyor...
powershell -NoProfile -Command ^
  "$ws=New-Object -ComObject WScript.Shell;" ^
  "$s=$ws.CreateShortcut([Environment]::GetFolderPath('Desktop')+'\NexusStart.lnk');" ^
  "$s.TargetPath='%OUT%\NexusStart.exe';" ^
  "$s.WorkingDirectory='%OUT%';" ^
  "$s.Description='NEXUS Start Menu v3.0';" ^
  "$s.Save()" >nul 2>nul
echo  [OK]
echo.

:: ── Sonuç ─────────────────────────────────────────────────────────────────
echo  ╔══════════════════════════════════════════════════════════════════╗
echo  ║  TAMAM!  dist\NexusStart.exe hazir                              ║
echo  ║                                                                  ║
echo  ║  v3.0 Yeni Ozellikler:                                          ║
echo  ║  - Acilis/kapanis animasyonu + Ripple + LED nabiz               ║
echo  ║  - Gece gokyuzu temasi + Neon glow modu                         ║
echo  ║  - Notlar, Yapilacaklar, Pomodoro, Geri sayim                   ║
echo  ║  - Hesap makinesi, Birim + Para doviz donusturucu                ║
echo  ║  - Pano gecmisi, Emoji ara, Renk toplayici                      ║
echo  ║  - Takvim, Analog saat, Coklu saat dilimi                       ║
echo  ║  - Web arama, QR kod, Sifre ureteci                             ║
echo  ║  - Klasor gruplari, Favoriler, Kullanim istatistigi             ║
echo  ║  - Disk/Ag/Pil monitoru, Terminal baslatic                      ║
echo  ║  - Turkce / English dil destegi                                 ║
echo  ║  - Yedekleme ve geri yukleme                                    ║
echo  ║                                                                  ║
echo  ║  Ctrl+Space veya tray ikonu cift tikla                          ║
echo  ╚══════════════════════════════════════════════════════════════════╝
echo.
explorer "%OUT%"
pause
