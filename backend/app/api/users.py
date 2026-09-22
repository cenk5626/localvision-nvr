"""
LocalVision NVR - Kullanıcı Yönetimi API'si (Users API).
Sadece Yönetici (Admin) rolü tarafından erişilebilir.
Rol Tabanlı Yetkilendirme (RBAC) ve kamera erişim kısıtlamalarını yönetir.
"""

import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.constants import AuditAction, UserRole
from app.core.database import get_db
from app.core.security import security
from app.models.audit import AuditLog
from app.models.user import User

router = APIRouter(prefix="/api/users", tags=["Kullanıcı Yönetimi"])


class UserCreateRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str = UserRole.USER.value
    allowed_camera_ids: List[int] = []


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    allowed_camera_ids: Optional[List[int]] = None
    new_password: Optional[str] = None


@router.get("")
async def list_users(
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Tüm kayıtlı kullanıcıları listeler."""
    stmt = select(User).order_by(User.id.asc())
    result = await db.execute(stmt)
    users = result.scalars().all()

    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "is_active": u.is_active,
            "allowed_camera_ids": u.allowed_camera_ids,
            "created_at": u.created_at.isoformat()
        }
        for u in users
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreateRequest,
    request: Request,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Yeni kullanıcı oluşturur."""
    # Kullanıcı adı kontrolü
    stmt = select(User).where(User.username == payload.username)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Bu kullanıcı adı zaten kullanımda.")

    new_user = User(
        username=payload.username,
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=security.hash_password(payload.password),
        role=payload.role,
        is_active=True,
        allowed_camera_ids_json=json.dumps(payload.allowed_camera_ids)
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Denetim günlüğü
    client_ip = request.client.host if request.client else "unknown"
    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action=AuditAction.USER_CREATE.value,
        resource_type="user",
        resource_id=str(new_user.id),
        details_json=json.dumps({"username": new_user.username, "role": new_user.role}),
        ip_address=client_ip
    )
    db.add(audit)
    await db.commit()

    return {"status": "ok", "id": new_user.id, "message": "Kullanıcı başarıyla oluşturuldu."}


@router.put("/{user_id}")
async def update_user(
    user_id: int,
    payload: UserUpdateRequest,
    request: Request,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Kullanıcı bilgilerini, rolünü veya şifresini günceller."""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.email is not None:
        user.email = payload.email
    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.allowed_camera_ids is not None:
        user.allowed_camera_ids = payload.allowed_camera_ids
    if payload.new_password:
        user.hashed_password = security.hash_password(payload.new_password)

    await db.commit()

    # Denetim günlüğü
    client_ip = request.client.host if request.client else "unknown"
    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action=AuditAction.USER_UPDATE.value,
        resource_type="user",
        resource_id=str(user_id),
        details_json=json.dumps({"username": user.username, "role": user.role}),
        ip_address=client_ip
    )
    db.add(audit)
    await db.commit()

    return {"status": "ok", "message": "Kullanıcı güncellendi."}


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Kullanıcıyı siler (Kendini silmeyi engeller)."""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Kendi hesabınızı silemezsiniz.")

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    target_name = user.username
    await db.delete(user)

    # Denetim günlüğü
    client_ip = request.client.host if request.client else "unknown"
    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action=AuditAction.USER_DELETE.value,
        resource_type="user",
        resource_id=str(user_id),
        details_json=json.dumps({"username": target_name}),
        ip_address=client_ip
    )
    db.add(audit)
    await db.commit()

    return {"status": "ok", "message": f"{target_name} kullanıcısı silindi."}
