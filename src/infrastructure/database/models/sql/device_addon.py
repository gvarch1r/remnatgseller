from decimal import Decimal

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.enums import Currency

from .base import BaseSql
from .timestamp import TimestampMixin


class DeviceAddon(BaseSql, TimestampMixin):
    __tablename__ = "device_addons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_count: Mapped[int] = mapped_column(Integer, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)

    prices: Mapped[list["DeviceAddonPrice"]] = relationship(
        "DeviceAddonPrice",
        back_populates="device_addon",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class DeviceAddonPrice(BaseSql):
    __tablename__ = "device_addon_prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_addon_id: Mapped[int] = mapped_column(
        ForeignKey("device_addons.id", ondelete="CASCADE"),
        nullable=False,
    )
    currency: Mapped[Currency] = mapped_column(
        Enum(
            Currency,
            name="currency",
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
    )
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    device_addon: Mapped["DeviceAddon"] = relationship(
        "DeviceAddon",
        back_populates="prices",
    )
