from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.application.common.dao import DeviceAddonDao
from src.application.dto import DeviceAddonDto, DeviceAddonPriceDto
from src.core.enums import Currency
from src.infrastructure.database.models import DeviceAddon, DeviceAddonPrice


class DeviceAddonDaoImpl(DeviceAddonDao):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _to_dto(self, row: DeviceAddon) -> DeviceAddonDto:
        prices = [
            DeviceAddonPriceDto(
                id=p.id,
                device_addon_id=p.device_addon_id,
                currency=p.currency,
                price=p.price,
            )
            for p in row.prices
        ]
        return DeviceAddonDto(
            id=row.id,
            device_count=row.device_count,
            order_index=row.order_index,
            is_active=row.is_active,
            prices=prices,
        )

    async def get_by_id(self, addon_id: int) -> DeviceAddonDto | None:
        stmt = (
            select(DeviceAddon)
            .where(DeviceAddon.id == addon_id)
            .options(selectinload(DeviceAddon.prices))
        )
        row = await self.session.scalar(stmt)
        return self._to_dto(row) if row else None

    async def get_active(self) -> list[DeviceAddonDto]:
        stmt = (
            select(DeviceAddon)
            .where(DeviceAddon.is_active.is_(True))
            .options(selectinload(DeviceAddon.prices))
            .order_by(DeviceAddon.order_index.asc())
        )
        result = await self.session.scalars(stmt)
        rows = list(result.all())
        return [self._to_dto(r) for r in rows]

    async def list_all(self) -> list[DeviceAddonDto]:
        stmt = (
            select(DeviceAddon)
            .options(selectinload(DeviceAddon.prices))
            .order_by(DeviceAddon.order_index.asc())
        )
        result = await self.session.scalars(stmt)
        rows = list(result.all())
        return [self._to_dto(r) for r in rows]

    async def toggle_active(self, addon_id: int) -> bool:
        row = await self.session.get(DeviceAddon, addon_id)
        if row is None:
            raise ValueError(f"Device addon '{addon_id}' not found")
        row.is_active = not row.is_active
        return row.is_active

    async def create(
        self,
        device_count: int,
        prices: dict[Currency, Decimal],
    ) -> DeviceAddonDto:
        max_order = await self.session.scalar(
            select(func.coalesce(func.max(DeviceAddon.order_index), 0)),
        )
        order_index = int(max_order or 0) + 1
        addon = DeviceAddon(
            device_count=device_count,
            order_index=order_index,
            is_active=True,
        )
        self.session.add(addon)
        await self.session.flush()
        for currency, price in prices.items():
            self.session.add(
                DeviceAddonPrice(
                    device_addon_id=addon.id,
                    currency=currency,
                    price=price,
                ),
            )
        await self.session.flush()
        stmt = (
            select(DeviceAddon)
            .where(DeviceAddon.id == addon.id)
            .options(selectinload(DeviceAddon.prices))
        )
        row = await self.session.scalar(stmt)
        assert row is not None
        return self._to_dto(row)

    async def delete(self, addon_id: int) -> bool:
        row = await self.session.get(DeviceAddon, addon_id)
        if row is None:
            return False
        await self.session.delete(row)
        await self.session.flush()
        stmt = select(DeviceAddon).order_by(DeviceAddon.order_index.asc())
        result = await self.session.scalars(stmt)
        remaining = list(result.all())
        for i, r in enumerate(remaining, start=1):
            if r.order_index != i:
                r.order_index = i
        return True
