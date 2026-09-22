"""
LocalVision NVR - Asenkron Veritabanı ve Oturum Yönetimi (SQLAlchemy 2.0).
Varsayılan olarak yerel SQLite (WAL modu etkinleştirilmiş) kullanır;
PostgreSQL için bağlantı dizesi değiştirilerek sorunsuz ölçeklenir.
"""

from typing import AsyncGenerator
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings

# Veritabanı motoru oluştur
connect_args = {}
if "sqlite" in settings.DATABASE_URL:
    # SQLite eşzamanlı okuma/yazma için kilit parametresi
    connect_args["check_same_thread"] = False

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args=connect_args,
    future=True
)

# SQLite için WAL (Write-Ahead Logging) ve foreign key etkinleştirme
if "sqlite" in settings.DATABASE_URL:
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Asenkron oturum fabrikası
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# ORM Tablo Temel Sınıfı
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI rotaları için veritabanı oturum sağlayıcısı."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Tabloları oluşturur ve ilk yönetici kullanıcısını hazırlar."""
    # Modelleri içe aktar (Base.metadata tanıması için)
    import app.models.user  # noqa: F401
    import app.models.camera  # noqa: F401
    import app.models.event  # noqa: F401
    import app.models.recording  # noqa: F401
    import app.models.audit  # noqa: F401
    import app.models.storage_policy  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # İlk yöneticiyi kontrol et / oluştur
    from sqlalchemy import select
    from app.core.constants import UserRole
    from app.core.security import security
    from app.models.user import User

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.username == settings.FIRST_ADMIN_USERNAME)
        )
        admin = result.scalar_one_or_none()
        if not admin:
            new_admin = User(
                username=settings.FIRST_ADMIN_USERNAME,
                email=settings.FIRST_ADMIN_EMAIL,
                hashed_password=security.hash_password(settings.FIRST_ADMIN_PASSWORD),
                role=UserRole.ADMIN.value,
                is_active=True,
                full_name="Sistem Yöneticisi"
            )
            session.add(new_admin)
            await session.commit()
