from typing import Any, Optional

from sqlalchemy import func, select

from src.core.enums import PromocodeRewardType
from src.infrastructure.database.models.sql import Promocode, PromocodeActivation

from .base import BaseRepository


class PromocodeRepository(BaseRepository):
    async def create(self, promocode: Promocode) -> Promocode:
        return await self.create_instance(promocode)

    async def get(self, promocode_id: int) -> Optional[Promocode]:
        return await self._get_one(Promocode, Promocode.id == promocode_id)

    async def get_by_code(self, code: str) -> Optional[Promocode]:
        return await self._get_one(Promocode, Promocode.code == code)

    async def search_by_code(self, query: str) -> list[Promocode]:
        pattern = f"%{query}%"
        return await self._get_many(
            Promocode,
            Promocode.code.ilike(pattern),
        )

    async def get_all(self) -> list[Promocode]:
        return await self._get_many(Promocode)

    async def update(self, promocode_id: int, **data: Any) -> Optional[Promocode]:
        return await self._update(Promocode, Promocode.id == promocode_id, **data)

    async def delete(self, promocode_id: int) -> bool:
        return bool(await self._delete(Promocode, Promocode.id == promocode_id))

    async def filter_by_type(self, promocode_type: PromocodeRewardType) -> list[Promocode]:
        return await self._get_many(Promocode, Promocode.reward_type == promocode_type)

    async def filter_active(self, is_active: bool) -> list[Promocode]:
        return await self._get_many(Promocode, Promocode.is_active == is_active)

    async def count_activations(self, promocode_id: int) -> int:
        stmt = select(func.count()).select_from(PromocodeActivation).where(
            PromocodeActivation.promocode_id == promocode_id
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def has_user_activated(self, user_telegram_id: int, promocode_id: int) -> bool:
        stmt = select(PromocodeActivation).where(
            PromocodeActivation.user_telegram_id == user_telegram_id,
            PromocodeActivation.promocode_id == promocode_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create_activation(self, promocode_id: int, user_telegram_id: int) -> PromocodeActivation:
        activation = PromocodeActivation(
            promocode_id=promocode_id,
            user_telegram_id=user_telegram_id,
        )
        return await self.create_instance(activation)
