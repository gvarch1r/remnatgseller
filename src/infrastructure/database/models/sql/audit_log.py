from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, Enum, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.enums import AuditActionType

from .base import BaseSql
from .timestamp import TimestampMixin


class AuditLog(BaseSql, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    actor_telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    action_type: Mapped[AuditActionType] = mapped_column(
        Enum(
            AuditActionType,
            name="audit_action_type",
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
    )
    details: Mapped[str] = mapped_column(Text, nullable=False, default="")
