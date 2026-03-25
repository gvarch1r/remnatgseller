from typing import Any

from adaptix import Retort
from aiogram_dialog import DialogManager
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from src.application.common import TranslatorRunner
from src.application.common.dao import PlanDao, PromocodeDao
from src.application.dto import PlanDto, PromocodeDto
from src.core.constants import PROMOCODE_PENDING_PLAN_ID
from src.core.enums import PlanType, PromocodeRewardType
from src.core.utils.i18n_helpers import i18n_format_days, i18n_format_traffic_limit
from src.core.utils.i18n_keys import UtilKey


def _fmt_limit(i18n: TranslatorRunner, value: int | None) -> str:
    if value is None or value < 0:
        return i18n.get(UtilKey.UNLIMITED)
    return str(value)


def _pc_key() -> str:
    return PromocodeDto.__name__


def _ensure_promocode(dialog_manager: DialogManager, retort: Retort) -> PromocodeDto:
    raw = dialog_manager.dialog_data.get(_pc_key())
    if raw:
        return retort.load(raw, PromocodeDto)
    pc = PromocodeDto()
    dialog_manager.dialog_data[_pc_key()] = retort.dump(pc)
    return pc


@inject
async def configurator_getter(
    dialog_manager: DialogManager,
    retort: FromDishka[Retort],
    i18n: FromDishka[TranslatorRunner],
    **kwargs: Any,
) -> dict[str, Any]:
    promocode = _ensure_promocode(dialog_manager, retort)

    reward_display: str | int | None = promocode.reward
    if promocode.reward is not None:
        if promocode.reward_type == PromocodeRewardType.DURATION:
            k, kw = i18n_format_days(promocode.reward)
            reward_display = i18n.get(k, **kw)
        elif promocode.reward_type == PromocodeRewardType.TRAFFIC:
            tk, tkw = i18n_format_traffic_limit(promocode.reward)
            reward_display = i18n.get(tk, **tkw)

    lifetime_s = _fmt_limit(i18n, promocode.lifetime)
    max_act_s = _fmt_limit(i18n, promocode.max_activations)

    data: dict[str, Any] = {
        "code": promocode.code or "—",
        "is_active": 1 if promocode.is_active else 0,
        "promocode_type": promocode.reward_type,
        "reward": reward_display if reward_display is not None else "—",
        "lifetime": lifetime_s,
        "max_activations": max_act_s,
        "promocode_has_id": promocode.id is not None,
    }

    if promocode.plan:
        dk, dw = i18n_format_days(promocode.plan.duration)
        tk, tw = i18n_format_traffic_limit(promocode.plan.traffic_limit)
        data.update(
            {
                "plan_name": promocode.plan.name,
                "plan_type": promocode.plan.type,
                "plan_traffic_limit": i18n.get(tk, **tw),
                "plan_device_limit": str(promocode.plan.device_limit),
                "plan_duration": i18n.get(dk, **dw),
            }
        )
    elif promocode.reward_type == PromocodeRewardType.SUBSCRIPTION:
        data.update(
            {
                "plan_name": "—",
                "plan_type": PlanType.UNLIMITED,
                "plan_traffic_limit": "—",
                "plan_device_limit": "—",
                "plan_duration": "—",
            }
        )

    return data


@inject
async def list_getter(
    dialog_manager: DialogManager,
    promocode_dao: FromDishka[PromocodeDao],
    **kwargs: Any,
) -> dict[str, Any]:
    promocodes = await promocode_dao.get_all()
    items = [
        {
            "id": p.id,
            "code": p.code,
            "rtype": p.reward_type.name,
        }
        for p in promocodes
        if p.id is not None
    ]
    return {"promocodes": items}


@inject
async def search_results_getter(
    dialog_manager: DialogManager,
    **kwargs: Any,
) -> dict[str, Any]:
    raw = dialog_manager.dialog_data.get("promocode_search_results", [])
    items = []
    for r in raw:
        if isinstance(r, dict):
            rid = r.get("id")
            items.append(
                {
                    "id": rid,
                    "code": r.get("code", "—"),
                    "rtype": str(r.get("reward_type", "")),
                }
            )
    return {"search_results": items}


async def promocode_reward_types_getter(
    dialog_manager: DialogManager,
    **kwargs: Any,
) -> dict[str, Any]:
    return {"reward_types": list(PromocodeRewardType)}


@inject
async def promocode_reward_getter(
    dialog_manager: DialogManager,
    retort: FromDishka[Retort],
    **kwargs: Any,
) -> dict[str, Any]:
    promocode = _ensure_promocode(dialog_manager, retort)
    return {
        "promocode_type": promocode.reward_type,
        "needs_numeric_reward": promocode.reward_type != PromocodeRewardType.SUBSCRIPTION,
        "needs_subscription_plan": promocode.reward_type == PromocodeRewardType.SUBSCRIPTION,
    }


@inject
async def promocode_plan_pick_getter(
    dialog_manager: DialogManager,
    plan_dao: FromDishka[PlanDao],
    **kwargs: Any,
) -> dict[str, Any]:
    dialog_manager.dialog_data.pop(PROMOCODE_PENDING_PLAN_ID, None)
    plans = await plan_dao.get_all()
    items = [
        {"id": p.id, "name": p.name}
        for p in plans
        if p.is_active and p.id is not None
    ]
    return {"promocode_plans": items}


@inject
async def promocode_plan_duration_getter(
    dialog_manager: DialogManager,
    plan_dao: FromDishka[PlanDao],
    i18n: FromDishka[TranslatorRunner],
    **kwargs: Any,
) -> dict[str, Any]:
    raw_id = dialog_manager.dialog_data.get(PROMOCODE_PENDING_PLAN_ID)
    if raw_id is None:
        return {"plan_durations": [], "plan_name": "", "has_plan_durations": False}

    plan = await plan_dao.get_by_id(int(raw_id))
    if not plan:
        return {"plan_durations": [], "plan_name": "", "has_plan_durations": False}

    durations = []
    for d in plan.durations:
        k, kw = i18n_format_days(d.days)
        durations.append({"days": d.days, "caption": i18n.get(k, **kw)})

    return {
        "plan_durations": durations,
        "plan_name": plan.name,
        "has_plan_durations": bool(durations),
    }


@inject
async def promocode_delete_confirm_getter(
    dialog_manager: DialogManager,
    retort: FromDishka[Retort],
    **kwargs: Any,
) -> dict[str, Any]:
    promocode = _ensure_promocode(dialog_manager, retort)
    return {"delete_promocode_code": promocode.code or "—"}
