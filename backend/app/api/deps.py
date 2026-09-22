"""
LocalVision NVR - API Güvenlik ve Bağımlılık Katmanı (Dependencies).
- JWT Doğrulama ve Kullanıcı Çözümleme
- Rol Tabanlı Erişim Kontrolü (RBAC)
- Kamera İzin Denetleyicisi
"""

from typing import List, Optional
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import UserRole
from app.core.database import get_db
from app.core.security import security
from app.models.user import User

security_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    db: AsyncSession = Depends(get_db)
) -> User:
    """İstek başlığındaki Bearer token'ı çözümler ve aktif kullanıcıyı döner."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Giriş yapmanız gerekmektedir (Yetkilendirme başlığı eksik).",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = credentials.credentials
    try:
        payload = security.decode_access_token(token)
        username = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Geçersiz jeton yapısı."
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Veritabanından kullanıcıyı sorgula
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı bulunamadı."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kullanıcı hesabı devre dışı bırakılmış."
        )

    return user


def require_roles(allowed_roles: List[UserRole]):
    """Belirli rollere sahip kullanıcıların erişimine izin verir."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        allowed_values = [r.value for r in allowed_roles]
        if current_user.role not in allowed_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Bu işlem için yetkiniz bulunmamaktadır. Gereken roller: {allowed_values}"
            )
        return current_user
    return role_checker


def check_camera_access(user: User, camera_id: int) -> bool:
    """Kullanıcının belirtilen kamerayı görme yetkisi var mı?"""
    if user.role in (UserRole.ADMIN.value, UserRole.OPERATOR.value):
        return True
    allowed_ids = user.allowed_camera_ids
    return camera_id in allowed_ids
