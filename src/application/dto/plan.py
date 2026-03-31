from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Optional, Self
from uuid import UUID

from supn_remnawave_panel.remnapy_compat import TrafficLimitStrategy

from src.core.enums import Currency, PlanAvailability, PlanType

from .base import BaseDto, TimestampMixin, TrackableMixin


@dataclass(kw_only=True)
class PlanSnapshotDto:
    id: int

    name: str
    tag: Optional[str] = None

    type: PlanType
    traffic_limit_strategy: TrafficLimitStrategy = TrafficLimitStrategy.NO_RESET

    traffic_limit: int
    device_limit: int
    duration: int

    internal_squads: list[UUID] = field(default_factory=list)
    external_squad: Optional[UUID] = None

    is_trial: bool = False

    @classmethod
    def from_plan(cls, plan: "PlanDto", duration: int) -> Self:
        return cls(
            id=plan.id,  # type: ignore[arg-type]
            name=plan.name,
            tag=plan.tag,
            type=plan.type,
            traffic_limit_strategy=plan.traffic_limit_strategy,
            traffic_limit=plan.traffic_limit,
            device_limit=plan.device_limit,
            duration=duration,
            internal_squads=plan.internal_squads,
            external_squad=plan.external_squad,
            is_trial=plan.is_trial,
        )

    @classmethod
    def test(cls) -> "PlanSnapshotDto":
        return cls(
            id=-1,
            name="test",
            tag=None,
            type=PlanType.UNLIMITED,
            traffic_limit=0,
            device_limit=0,
            duration=0,
            traffic_limit_strategy=TrafficLimitStrategy.NO_RESET,
            internal_squads=[],
            external_squad=None,
        )

    @classmethod
    def from_device_addon(cls, device_count: int) -> "PlanSnapshotDto":
        return cls(
            id=-2,
            name=f"+{device_count}",
            tag=None,
            type=PlanType.DEVICES,
            traffic_limit=-1,
            device_limit=device_count,
            duration=0,
            traffic_limit_strategy=TrafficLimitStrategy.NO_RESET,
            internal_squads=[],
            external_squad=None,
        )

    @classmethod
    def from_stored_json(cls, data: dict[str, Any]) -> Self:
        strat = data["traffic_limit_strategy"]
        if isinstance(strat, str):
            strat = TrafficLimitStrategy(strat)
        ptype = data["type"]
        if isinstance(ptype, str):
            ptype = PlanType(ptype)
        squads = data.get("internal_squads") or []
        ext = data.get("external_squad")
        return cls(
            id=int(data["id"]),
            name=str(data["name"]),
            tag=data.get("tag"),
            type=ptype,
            traffic_limit_strategy=strat,
            traffic_limit=int(data["traffic_limit"]),
            device_limit=int(data["device_limit"]),
            duration=int(data.get("duration", 0)),
            internal_squads=[UUID(str(x)) for x in squads],
            external_squad=UUID(str(ext)) if ext else None,
            is_trial=bool(data.get("is_trial", False)),
        )

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "tag": self.tag,
            "type": self.type.name,
            "traffic_limit_strategy": self.traffic_limit_strategy.name,
            "traffic_limit": self.traffic_limit,
            "device_limit": self.device_limit,
            "duration": self.duration,
            "internal_squads": [str(u) for u in self.internal_squads],
            "external_squad": str(self.external_squad) if self.external_squad else None,
            "is_trial": self.is_trial,
        }


@dataclass(kw_only=True)
class PlanDto(BaseDto, TrackableMixin, TimestampMixin):
    public_code: Optional[str] = None
    name: str = "Default Plan"
    description: Optional[str] = None
    tag: Optional[str] = None

    type: PlanType = PlanType.BOTH
    availability: PlanAvailability = PlanAvailability.ALL
    traffic_limit_strategy: TrafficLimitStrategy = TrafficLimitStrategy.NO_RESET

    traffic_limit: int = 100
    device_limit: int = 1

    allowed_user_ids: list[int] = field(default_factory=list)
    internal_squads: list[UUID] = field(default_factory=list)
    external_squad: Optional[UUID] = None

    order_index: int = 0
    is_active: bool = False
    is_trial: bool = False

    durations: list["PlanDurationDto"] = field(default_factory=list)

    @property
    def is_unlimited_traffic(self) -> bool:
        return self.type not in {PlanType.TRAFFIC, PlanType.BOTH}

    @property
    def is_unlimited_devices(self) -> bool:
        return self.type not in {PlanType.DEVICES, PlanType.BOTH}

    def get_duration(self, days: int) -> Optional["PlanDurationDto"]:
        return next((d for d in self.durations if d.days == days), None)


@dataclass(kw_only=True)
class PlanDurationDto(BaseDto, TrackableMixin):
    days: int
    order_index: int = 0
    prices: list["PlanPriceDto"] = field(default_factory=list)

    def get_price(self, currency: Currency) -> Decimal:
        return next((p.price for p in self.prices if p.currency == currency))


@dataclass(kw_only=True)
class PlanPriceDto(BaseDto, TrackableMixin):
    currency: Currency
    price: Decimal
