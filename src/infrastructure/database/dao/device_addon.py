from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.application.common.dao import DeviceAddonDao
from src.application.dto import DeviceAddonDto, DeviceAddonPriceDto
from src.infrastructure.database.models import DeviceAddon


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
