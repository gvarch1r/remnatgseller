from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from src.core.enums import PromocodeRewardType
from src.core.utils.time import datetime_now

from .base import BaseDto, TimestampMixin
from .plan import PlanSnapshotDto


@dataclass(kw_only=True)
class PromocodeDto(BaseDto, TimestampMixin):
    code: str = ""
    is_active: bool = True
    reward_type: PromocodeRewardType = PromocodeRewardType.PERSONAL_DISCOUNT
    reward: Optional[int] = None
    plan: Optional[PlanSnapshotDto] = None
    lifetime: Optional[int] = -1
    max_activations: Optional[int] = -1

    @property
    def is_expired(self) -> bool:
        if self.lifetime is None or self.lifetime < 0 or self.created_at is None:
            return False
        return datetime_now() > self.created_at + timedelta(days=self.lifetime)
