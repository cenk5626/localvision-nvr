"""
LocalVision NVR - Uçtan Uca REST API Entegrasyon Testleri.
"""

from httpx import ASGITransport, AsyncClient
import pytest
from app.core.config import settings
from app.core.database import init_db
from app.main import app


@pytest.mark.asyncio
async def test_root_endpoint():
    """Kök dizin erişimi ve gizlilik beyanı testi."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["app"] == settings.APP_NAME
        assert "Privacy-by-Design" in data["privacy"]


@pytest.mark.asyncio
async def test_system_health():
    """Sistem sağlık kontrolü endpoint testi."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/system/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "cpu_percent" in data
        assert "disk" in data


@pytest.mark.asyncio
async def test_privacy_checklist_endpoint():
    """Gizlilik ve KVKK kontrol listesi doğrulaması."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/system/privacy-checklist")
        assert response.status_code == 200
        data = response.json()
        assert data["features"]["facial_recognition"] is False
        assert data["features"]["biometric_profiling"] is False
        assert data["features"]["cloud_data_transfer"] is False


@pytest.mark.asyncio
async def test_auth_login_and_me():
    """Yönetici girişi ve /me profil testi."""
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Başarılı Giriş
        login_res = await client.post(
            "/api/auth/login",
            json={
                "username": settings.FIRST_ADMIN_USERNAME,
                "password": settings.FIRST_ADMIN_PASSWORD
            }
        )
        assert login_res.status_code == 200
        token_data = login_res.json()
        assert "access_token" in token_data
        assert token_data["role"] == "admin"

        token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. /me Profil Sorgusu
        me_res = await client.get("/api/auth/me", headers=headers)
        assert me_res.status_code == 200
        me_data = me_res.json()
        assert me_data["username"] == settings.FIRST_ADMIN_USERNAME
        assert me_data["role"] == "admin"


@pytest.mark.asyncio
async def test_webcam_discovery():
    """Yerel web kamerası keşfi endpoint testi."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Önce giriş yap
        login_res = await client.post(
            "/api/auth/login",
            json={
                "username": settings.FIRST_ADMIN_USERNAME,
                "password": settings.FIRST_ADMIN_PASSWORD
            }
        )
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Web kameralarını sorgula
        resp = await client.get("/api/cameras/discover-webcams", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "webcams" in data
