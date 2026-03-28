from typing import Any

from aiogram_dialog import DialogManager
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from src.application.common.dao import DeviceAddonDao


def _price_summary(prices: list) -> str:
    parts = [f"{p.price}{p.currency.symbol}" for p in prices]
    return " · ".join(parts) if parts else "—"


@inject
async def device_addons_admin_getter(
    dialog_manager: DialogManager,
    device_addon_dao: FromDishka[DeviceAddonDao],
    **kwargs: Any,
) -> dict[str, Any]:
    del dialog_manager, kwargs
    addons = await device_addon_dao.list_all()
    items = [
        {
            "id": a.id,
            "device_count": a.device_count,
            "summary": _price_summary(a.prices),
            "is_active": a.is_active,
        }
        for a in addons
    ]
    return {"device_addons": items, "addons_empty": len(items) == 0}
