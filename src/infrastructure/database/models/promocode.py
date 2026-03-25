from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.enums import PromocodeRewardType

from .base import BaseSql
from .timestamp import NOW_FUNC, TimestampMixin


class Promocode(BaseSql, TimestampMixin):
    __tablename__ = "promocodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reward_type: Mapped[PromocodeRewardType] = mapped_column(nullable=False)
    reward: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    plan: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    lifetime: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_activations: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class PromocodeActivation(BaseSql):
    __tablename__ = "promocode_activations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    promocode_id: Mapped[int] = mapped_column(Integer, ForeignKey("promocodes.id"), nullable=False)
    user_telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id"),
        nullable=False,
    )
    activated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=NOW_FUNC,
        nullable=False,
    )
