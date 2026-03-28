from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from src.core.enums import Currency

from .base import BaseDto, TrackableMixin


@dataclass(frozen=True)
class CreateDeviceAddonDto:
    device_count: int
    prices: dict[Currency, Decimal]


@dataclass(kw_only=True)
class DeviceAddonPriceDto(BaseDto, TrackableMixin):
    device_addon_id: int
    currency: Currency
    price: Decimal


@dataclass(kw_only=True)
class DeviceAddonDto(BaseDto, TrackableMixin):
    device_count: int
    order_index: int = 0
    is_active: bool = True
    prices: list[DeviceAddonPriceDto] = field(default_factory=list)

    def get_price(self, currency: Currency) -> Optional[Decimal]:
        for p in self.prices:
            if p.currency == currency:
                return p.price
        return None
