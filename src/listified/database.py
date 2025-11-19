"""Database configuration and SQLAlchemy models for Listified."""

from datetime import UTC, datetime
from uuid import UUID as PYUUID

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from .settings import settings


def _utcnow() -> datetime:
    """Get current UTC datetime.

    Returns:
        Current datetime in UTC timezone.
    """
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


class List(Base):
    """SQLAlchemy model for the list table.

    Represents a to-do list that can contain multiple items.
    """

    __tablename__ = "list"

    id: Mapped[PYUUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Item(Base):
    """SQLAlchemy model for the items table.

    Represents an individual item within a list.
    """

    __tablename__ = "items"

    id: Mapped[PYUUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    list_id: Mapped[PYUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("list.id"))
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    order: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# Create async engine
engine = create_async_engine(
    settings.POSTGRES_DSN,
    echo=settings.DEBUG,
    future=True,
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    future=True,  # type: ignore[arg-type]
)


async def get_db():  # type: ignore[misc]
    """Get an async database session.

    Yields:
        An async SQLAlchemy session instance.
    """
    async with AsyncSessionLocal() as session:
        yield session
