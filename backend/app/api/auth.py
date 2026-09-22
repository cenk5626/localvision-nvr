"""
LocalVision NVR - Kimlik Doğrulama ve Oturum API'si.
- Bcrypt parola doğrulaması
- Brute-force koruması (5 hatalı deneme -> 15 dakika kilit)
- JWT erişim jetonu üretimi
- Denetim günlüğü (Audit log) kaydı
"""

from datetime import datetime, timedelta, timezone
import json
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.constants import AuditAction, SystemDefaults, UserRole
from app.core.database import get_db
from app.core.security import security
from app.models.audit import AuditLog
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["Kimlik Doğrulama"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    role: str
    full_name: Optional[str] = None
    allowed_camera_ids: list[int]
    preferences: Dict[str, Any]


class PreferencesUpdateRequest(BaseModel):
    preferences: Dict[str, Any]


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Kullanıcı girişi yapar ve JWT jetonu döndürür."""
    client_ip = request.client.host if request.client else "unknown"

    # Kullanıcıyı ara
    stmt = select(User).where(User.username == payload.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)

    if not user:
        # Sahte zamanlama ile kaba kuvveti yavaşlat
        security.verify_password("dummy", "$2b$12$dummyhashdummyhashdummyhashdummyhashdummyhashdummyha")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı adı veya parola hatalı."
        )

    # Hesap kilitli mi kontrol et
    if user.locked_until and user.locked_until > now:
        remaining_minutes = int((user.locked_until - now).total_seconds() / 60) + 1
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Çok fazla hatalı deneme nedeniyle hesap kilitlendi. Lütfen {remaining_minutes} dakika sonra tekrar deneyin."
        )

    # Parolayı doğrula
    if not security.verify_password(payload.password, user.hashed_password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= SystemDefaults.MAX_FAILED_LOGIN_ATTEMPTS:
            user.locked_until = now + timedelta(minutes=SystemDefaults.ACCOUNT_LOCKOUT_MINUTES)

        # Başarısız denetim kaydı
        audit = AuditLog(
            user_id=user.id,
            username=user.username,
            action=AuditAction.AUTH_LOGIN_FAILED.value,
            ip_address=client_ip,
            details_json=json.dumps({"attempt": user.failed_login_attempts})
        )
        db.add(audit)
        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı adı veya parola hatalı."
        )

    # Başarılı giriş: Hatalı sayaçları sıfırla
    user.failed_login_attempts = 0
    user.locked_until = None

    token = security.create_access_token(
        subject=user.username,
        role=UserRole(user.role),
        extra_claims={"user_id": user.id}
    )

    # Başarılı denetim kaydı
    audit = AuditLog(
        user_id=user.id,
        username=user.username,
        action=AuditAction.AUTH_LOGIN.value,
        ip_address=client_ip
    )
    db.add(audit)
    await db.commit()

    user_prefs = {}
    try:
        user_prefs = json.loads(user.preferences_json or "{}")
    except Exception:
        pass

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        username=user.username,
        role=user.role,
        full_name=user.full_name,
        allowed_camera_ids=user.allowed_camera_ids,
        preferences=user_prefs
    )


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Mevcut oturum sahibinin profil ve yetki bilgilerini döndürür."""
    user_prefs = {}
    try:
        user_prefs = json.loads(current_user.preferences_json or "{}")
    except Exception:
        pass

    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "allowed_camera_ids": current_user.allowed_camera_ids,
        "preferences": user_prefs,
        "created_at": current_user.created_at.isoformat()
    }


@router.put("/preferences")
async def update_preferences(
    payload: PreferencesUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Kullanıcının görünüm ve arayüz tercihlerini kaydeder."""
    current_user.preferences_json = json.dumps(payload.preferences)
    await db.commit()
    return {"status": "ok", "message": "Tercihler güncellendi."}
