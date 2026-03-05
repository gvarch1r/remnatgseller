from typing import Any

from aiogram_dialog import DialogManager
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from src.core.enums import Currency
from src.core.utils.adapter import DialogDataAdapter
from src.infrastructure.database.models.dto import DeviceAddonDto
from src.services.device_addon import DeviceAddonService


@inject
async def addons_getter(
    dialog_manager: DialogManager,
    device_addon_service: FromDishka[DeviceAddonService],
    **kwargs: Any,
) -> dict[str, Any]:
    addons = await device_addon_service.get_all()
    formatted = [
        {
            "id": a.id,
            "device_count": a.device_count,
            "is_active": a.is_active,
            "prices_str": ", ".join(
                f"{p.currency.symbol}: {p.price}" for p in a.prices
            ),
        }
        for a in addons
    ]
    return {"addons": formatted}


async def edit_getter(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    adapter = DialogDataAdapter(dialog_manager)
    addon = adapter.load(DeviceAddonDto)
    if not addon:
        return {"addon": None, "prices": [], "currency_list": []}

    prices = [
        {"currency": p.currency.value, "symbol": p.currency.symbol, "price": str(p.price)}
        for p in addon.prices
    ]
    return {
        "addon": {
            "id": addon.id,
            "device_count": addon.device_count,
            "is_active": addon.is_active,
        },
        "prices": prices,
        "currency_list": [{"currency": c.value, "symbol": c.symbol} for c in Currency],
    }


async def price_getter(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    adapter = DialogDataAdapter(dialog_manager)
    addon = adapter.load(DeviceAddonDto)
    selected = dialog_manager.dialog_data.get("selected_currency")
    if not addon or not selected:
        return {"currency": "—", "current_price": ""}
    currency = Currency(selected)
    price = addon.get_price(currency)
    return {
        "currency": currency.symbol,
        "current_price": str(price) if price is not None else "",
    }
