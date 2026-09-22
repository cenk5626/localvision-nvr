#!/usr/bin/env bash
set -e

echo "======================================================================="
echo "         LocalVision NVR - Akıllı Video Güvenlik Sistemi"
echo "         Linux Sunucu Başlatıcı"
echo "======================================================================="

# Dizin geçişi
cd "$(dirname "$0")"

# Gereksinim denetimi
if ! command -v python3 &> /dev/null; then
    echo "HATA: python3 bulunamadı!"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "HATA: node bulunamadı!"
    exit 1
fi

echo "[1/2] Backend başlatılıyor (Port 8000)..."
python3 backend/run_server.py &
BACKEND_PID=$!

echo "[2/2] Frontend başlatılıyor (Port 5173)..."
cd frontend && npm run dev &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT SIGTERM

echo "LocalVision NVR aktif: http://localhost:5173"
wait
