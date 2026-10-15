from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class FileRecord(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    file_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )

    original_filename: Mapped[str] = mapped_column(
        String(255), nullable=False
    )

    storage_filename: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), index=True, nullable=False
    )

    encrypted: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )