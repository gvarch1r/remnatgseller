from typing import Any

from aiogram_dialog import DialogManager
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from src.core.constants import PROMOCODE_PENDING_PLAN_ID
from src.core.enums import PlanType, PromocodeAvailability, PromocodeRewardType
from src.core.utils.adapter import DialogDataAdapter
from src.core.utils.formatters import i18n_format_days, i18n_format_limit, i18n_format_traffic_limit
from src.infrastructure.database.models.dto import PromocodeDto
from src.services.plan import PlanService
from src.services.promocode import PromocodeService


async def configurator_getter(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    adapter = DialogDataAdapter(dialog_manager)
    promocode = adapter.load(PromocodeDto)

    if promocode is None:
        promocode = PromocodeDto()
        adapter.save(promocode)

    data = promocode.model_dump()

    if promocode.reward:
        if promocode.reward_type == PromocodeRewardType.DURATION:
            reward = i18n_format_days(promocode.reward)
            data.update({"reward": reward})
        elif promocode.reward_type == PromocodeRewardType.TRAFFIC:
            reward = i18n_format_traffic_limit(promocode.reward)
            data.update({"reward": reward})

    helpers = {
        "promocode_type": promocode.reward_type,
        "availability_type": promocode.availability,
        "max_activations": i18n_format_limit(promocode.max_activations),
        "lifetime": i18n_format_days(promocode.lifetime),
    }

    if promocode.plan:
        plan = {
            "plan_name": promocode.plan.name,
            "plan_type": promocode.plan.type,
            "plan_traffic_limit": promocode.plan.traffic_limit,
            "plan_device_limit": promocode.plan.device_limit,
            "plan_duration": promocode.plan.duration,
        }
        data.update(plan)
    elif promocode.reward_type == PromocodeRewardType.SUBSCRIPTION:
        # Нет снимка плана — иначе { frg-plan-snapshot } / plan-type ломают Fluent (FluentNone)
        data.update(
            {
                "plan_name": "—",
                "plan_type": PlanType.UNLIMITED,
                "plan_traffic_limit": "—",
                "plan_device_limit": "—",
                "plan_duration": "—",
            }
        )

    data.update(helpers)

    return data


@inject
async def list_getter(
    dialog_manager: DialogManager,
    promocode_service: FromDishka[PromocodeService],
    **kwargs: Any,
) -> dict[str, Any]:
    promocodes = await promocode_service.get_all()
    items = [
        {
            "id": p.id,
            "code": p.code,
            "is_active": p.is_active,
            "reward_type": p.reward_type,
        }
        for p in promocodes
    ]
    return {"promocodes": items}


async def search_results_getter(
    dialog_manager: DialogManager,
    **kwargs: Any,
) -> dict[str, Any]:
    raw = dialog_manager.dialog_data.get("search_results", [])
    items = [r if isinstance(r, dict) else PromocodeDto.model_validate(r).model_dump(mode="json") for r in raw]
    return {"search_results": items}


async def promocode_reward_types_getter(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    return {"reward_types": list(PromocodeRewardType)}


async def promocode_availabilities_getter(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    return {"availabilities": list(PromocodeAvailability)}


async def promocode_reward_getter(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    adapter = DialogDataAdapter(dialog_manager)
    promocode = adapter.load(PromocodeDto) or PromocodeDto()
    return {
        "reward_type": promocode.reward_type,
        "needs_numeric_reward": promocode.reward_type != PromocodeRewardType.SUBSCRIPTION,
        "needs_subscription_plan": promocode.reward_type == PromocodeRewardType.SUBSCRIPTION,
    }


@inject
async def promocode_plan_pick_getter(
    dialog_manager: DialogManager,
    plan_service: FromDishka[PlanService],
    **kwargs: Any,
) -> dict[str, Any]:
    dialog_manager.dialog_data.pop(PROMOCODE_PENDING_PLAN_ID, None)
    plans = await plan_service.get_all()
    items = [
        {"id": p.id, "name": p.name}
        for p in plans
        if p.is_active and p.id is not None
    ]
    return {"promocode_plans": items}


@inject
async def promocode_plan_duration_getter(
    dialog_manager: DialogManager,
    plan_service: FromDishka[PlanService],
    **kwargs: Any,
) -> dict[str, Any]:
    raw_id = dialog_manager.dialog_data.get(PROMOCODE_PENDING_PLAN_ID)
    if raw_id is None:
        return {"plan_durations": [], "plan_name": "", "has_plan_durations": False}

    plan = await plan_service.get(int(raw_id))
    if not plan:
        return {"plan_durations": [], "plan_name": "", "has_plan_durations": False}

    items = [
        {
            "days": d.days,
            "caption": "∞" if d.days == -1 else f"{d.days} дн.",
        }
        for d in plan.durations
    ]
    return {
        "plan_durations": items,
        "plan_name": plan.name,
        "has_plan_durations": bool(items),
    }
