from typing import Optional

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.common.dao import PromocodeDao
from src.application.dto import PlanSnapshotDto, PromocodeDto
from src.infrastructure.database.models import Promocode, PromocodeActivation


def _norm_optional_int(value: Optional[int]) -> Optional[int]:
    if value is None or value < 0:
        return None
    return value


class PromocodeDaoImpl(PromocodeDao):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _to_dto(self, row: Promocode) -> PromocodeDto:
        plan = PlanSnapshotDto.from_stored_json(row.plan) if row.plan else None
        lifetime = row.lifetime if row.lifetime is not None else -1
        max_act = row.max_activations if row.max_activations is not None else -1
        return PromocodeDto(
            id=row.id,
            code=row.code,
            is_active=row.is_active,
            reward_type=row.reward_type,
            reward=row.reward,
            plan=plan,
            lifetime=lifetime,
            max_activations=max_act,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def get_by_id(self, promocode_id: int) -> Optional[PromocodeDto]:
        row = await self.session.get(Promocode, promocode_id)
        return self._to_dto(row) if row else None

    async def get_by_code(self, code: str) -> Optional[PromocodeDto]:
        stmt = select(Promocode).where(Promocode.code == code)
        row = await self.session.scalar(stmt)
        return self._to_dto(row) if row else None

    async def get_all(self) -> list[PromocodeDto]:
        stmt = select(Promocode).order_by(Promocode.id.desc())
        result = await self.session.scalars(stmt)
        return [self._to_dto(r) for r in result.all()]

    async def search_by_code(self, query: str) -> list[PromocodeDto]:
        pattern = f"%{query}%"
        stmt = select(Promocode).where(Promocode.code.ilike(pattern)).order_by(Promocode.id.desc())
        result = await self.session.scalars(stmt)
        return [self._to_dto(r) for r in result.all()]

    async def create(self, promocode: PromocodeDto) -> PromocodeDto:
        row = Promocode(
            code=promocode.code,
            is_active=promocode.is_active,
            reward_type=promocode.reward_type,
            reward=promocode.reward,
            plan=promocode.plan.to_json_dict() if promocode.plan else None,
            lifetime=_norm_optional_int(promocode.lifetime),
            max_activations=_norm_optional_int(promocode.max_activations),
        )
        self.session.add(row)
        await self.session.flush()
        return self._to_dto(row)

    async def update(self, promocode: PromocodeDto) -> Optional[PromocodeDto]:
        if promocode.id is None:
            return None
        row = await self.session.get(Promocode, promocode.id)
        if not row:
            return None
        row.code = promocode.code
        row.is_active = promocode.is_active
        row.reward_type = promocode.reward_type
        row.reward = promocode.reward
        row.plan = promocode.plan.to_json_dict() if promocode.plan else None
        row.lifetime = _norm_optional_int(promocode.lifetime)
        row.max_activations = _norm_optional_int(promocode.max_activations)
        await self.session.flush()
        return self._to_dto(row)

    async def delete(self, promocode_id: int) -> bool:
        await self.session.execute(
            delete(PromocodeActivation).where(PromocodeActivation.promocode_id == promocode_id)
        )
        stmt = delete(Promocode).where(Promocode.id == promocode_id).returning(Promocode.id)
        result = await self.session.execute(stmt)
        deleted_id = result.scalar_one_or_none()
        return deleted_id is not None

    async def count_activations(self, promocode_id: int) -> int:
        stmt = select(func.count()).select_from(PromocodeActivation).where(
            PromocodeActivation.promocode_id == promocode_id
        )
        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)

    async def has_user_activated(self, user_telegram_id: int, promocode_id: int) -> bool:
        stmt = select(PromocodeActivation.id).where(
            PromocodeActivation.user_telegram_id == user_telegram_id,
            PromocodeActivation.promocode_id == promocode_id,
        )
        row = await self.session.scalar(stmt)
        return row is not None

    async def create_activation(self, promocode_id: int, user_telegram_id: int) -> None:
        act = PromocodeActivation(promocode_id=promocode_id, user_telegram_id=user_telegram_id)
        self.session.add(act)
        await self.session.flush()
