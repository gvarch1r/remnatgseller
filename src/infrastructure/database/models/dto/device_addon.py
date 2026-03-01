from decimal import Decimal
from typing import Optional

from pydantic import Field

from src.core.enums import Currency

from .base import TrackableDto


class DeviceAddonPriceDto(TrackableDto):
    id: Optional[int] = Field(default=None, frozen=True)
    device_addon_id: int
    currency: Currency
    price: Decimal


class DeviceAddonDto(TrackableDto):
    id: Optional[int] = Field(default=None, frozen=True)
    device_count: int
    order_index: int = 0
    is_active: bool = True
    prices: list[DeviceAddonPriceDto] = []

    def get_price(self, currency: Currency) -> Optional[Decimal]:
        for p in self.prices:
            if p.currency == currency:
                return p.price
        return None
