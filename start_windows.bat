@echo off
chcp 65001 > nul
cls
echo =======================================================================
echo          LocalVision NVR - Akıllı Video Güvenlik Sistemi
echo          Yerel Ağ Odaklı & Gizlilik Tasarımlı VMS Başlatıcı
echo =======================================================================
echo.

cd /d "%~dp0"

echo [1/3] Sistem gereksinimleri kontrol ediliyor...
python --version >nul 2>&1
if errorlevel 1 (
    echo HATA: Python bulunamadı! Lütfen Python 3.11 veya 3.12 yükleyin.
    pause
    exit /b
)

node --version >nul 2>&1
if errorlevel 1 (
    echo HATA: Node.js bulunamadı! Lütfen Node.js yükleyin.
    pause
    exit /b
)

echo [2/3] Backend API ve Video Motoru başlatılıyor (Port 8000)...
start "LocalVision NVR Backend" cmd /k "cd /d %~dp0 && python backend/run_server.py"

echo [3/3] Frontend Web Yönetim Paneli başlatılıyor (Port 5173)...
start "LocalVision NVR Web Panel" cmd /k "cd /d %~dp0\frontend && npm run dev"

timeout /t 3 > nul

echo.
echo =======================================================================
echo   Sistem Başlatıldı!
echo   Web Yönetim Paneli: http://localhost:5173
echo   Swagger API Belgeleri: http://localhost:8000/docs
echo   Giriş Bilgileri: admin / Admin*LocalVision2026!
echo =======================================================================
echo.

start http://localhost:5173
