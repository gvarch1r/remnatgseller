from typing import Any, cast

from aiogram_dialog import DialogManager
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject
from fluentogram import TranslatorRunner

from src.core.config import AppConfig
from src.core.enums import PurchaseType
from src.core.utils.adapter import DialogDataAdapter
from src.core.utils.formatters import (
    i18n_format_days,
    i18n_format_device_limit,
    i18n_format_expire_time,
    i18n_format_traffic_limit,
)
from src.infrastructure.database.models.dto import (
    DeviceAddonDto,
    PlanDto,
    PriceDetailsDto,
    UserDto,
)
from src.services.device_addon import DeviceAddonService
from src.services.payment_gateway import PaymentGatewayService
from src.services.plan import PlanService
from src.services.pricing import PricingService
from src.services.settings import SettingsService


@inject
async def subscription_getter(
    dialog_manager: DialogManager,
    user: UserDto,
    **kwargs: Any,
) -> dict[str, Any]:
    has_active = bool(user.current_subscription and not user.current_subscription.is_trial)
    is_unlimited = user.current_subscription.is_unlimited if user.current_subscription else False
    has_devices_limit = (
        user.current_subscription.has_devices_limit if user.current_subscription else False
    )
    return {
        "has_active_subscription": has_active,
        "is_not_unlimited": not is_unlimited,
        "has_devices_limit": has_devices_limit,
    }


@inject
async def device_addons_getter(
    dialog_manager: DialogManager,
    device_addon_service: FromDishka[DeviceAddonService],
    settings_service: FromDishka[SettingsService],
    pricing_service: FromDishka[PricingService],
    user: UserDto,
    **kwargs: Any,
) -> dict[str, Any]:
    addons = await device_addon_service.get_active()
    currency = await settings_service.get_default_currency()
    formatted = []
    for addon in addons:
        price = addon.get_price(currency)
        if price is None:
            continue
        pricing = pricing_service.calculate(user, price, currency)
        formatted.append(
            {
                "id": addon.id,
                "device_count": addon.device_count,
                "final_amount": pricing.final_amount,
                "discount_percent": pricing.discount_percent,
                "original_amount": pricing.original_amount,
                "currency": currency.symbol,
            }
        )
    return {"device_addons": formatted}


@inject
async def plans_getter(
    dialog_manager: DialogManager,
    user: UserDto,
    plan_service: FromDishka[PlanService],
    **kwargs: Any,
) -> dict[str, Any]:
    plans = await plan_service.get_available_plans(user)

    formatted_plans = [
        {
            "id": plan.id,
            "name": plan.name,
        }
        for plan in plans
    ]

    return {
        "plans": formatted_plans,
    }


@inject
async def duration_getter(
    dialog_manager: DialogManager,
    user: UserDto,
    i18n: FromDishka[TranslatorRunner],
    settings_service: FromDishka[SettingsService],
    pricing_service: FromDishka[PricingService],
    **kwargs: Any,
) -> dict[str, Any]:
    adapter = DialogDataAdapter(dialog_manager)
    plan = adapter.load(PlanDto)

    if not plan:
        raise ValueError("PlanDto not found in dialog data")

    currency = await settings_service.get_default_currency()
    only_single_plan = dialog_manager.dialog_data.get("only_single_plan", False)
    dialog_manager.dialog_data["is_free"] = False
    durations = []

    for duration in plan.durations:
        key, kw = i18n_format_days(duration.days)
        price = pricing_service.calculate(user, duration.get_price(currency), currency)
        durations.append(
            {
                "days": duration.days,
                "period": i18n.get(key, **kw),
                "final_amount": price.final_amount,
                "discount_percent": price.discount_percent,
                "original_amount": price.original_amount,
                "currency": currency.symbol,
            }
        )

    return {
        "plan": plan.name,
        "description": plan.description or False,
        "type": plan.type,
        "devices": i18n_format_device_limit(plan.device_limit),
        "traffic": i18n_format_traffic_limit(plan.traffic_limit),
        "durations": durations,
        "period": 0,
        "final_amount": 0,
        "currency": "",
        "only_single_plan": only_single_plan,
    }


@inject
async def payment_method_getter(
    dialog_manager: DialogManager,
    payment_gateway_service: FromDishka[PaymentGatewayService],
    i18n: FromDishka[TranslatorRunner],
    **kwargs: Any,
) -> dict[str, Any]:
    adapter = DialogDataAdapter(dialog_manager)
    purchase_type = dialog_manager.dialog_data.get("purchase_type")
    gateways = await payment_gateway_service.filter_active()

    if purchase_type == PurchaseType.ADD_DEVICES:
        addon = adapter.load(DeviceAddonDto)
        if not addon:
            raise ValueError("DeviceAddonDto not found in dialog data")
        payment_methods = []
        for gateway in gateways:
            price = addon.get_price(gateway.currency)
            if price is not None:
                payment_methods.append(
                    {
                        "gateway_type": gateway.type,
                        "price": price,
                        "currency": gateway.currency.symbol,
                    }
                )
        period_key, period_kw = i18n_format_device_limit(addon.device_count)
        devices_str = i18n.get(period_key, **period_kw)
        return {
            "plan": f"+{addon.device_count}",
            "description": False,
            "type": None,
            "devices": devices_str,
            "traffic": i18n_format_traffic_limit(-1),
            "period": f"+{addon.device_count}",
            "payment_methods": payment_methods,
            "final_amount": 0,
            "currency": "",
            "only_single_duration": False,
            "is_add_devices": True,
        }

    plan = adapter.load(PlanDto)
    if not plan:
        raise ValueError("PlanDto not found in dialog data")
    selected_duration = dialog_manager.dialog_data["selected_duration"]
    only_single_duration = dialog_manager.dialog_data.get("only_single_duration", False)
    duration = plan.get_duration(selected_duration)
    if not duration:
        raise ValueError(f"Duration '{selected_duration}' not found in plan '{plan.name}'")
    payment_methods = []
    for gateway in gateways:
        payment_methods.append(
            {
                "gateway_type": gateway.type,
                "price": duration.get_price(gateway.currency),
                "currency": gateway.currency.symbol,
            }
        )
    key, kw = i18n_format_days(duration.days)
    return {
        "plan": plan.name,
        "description": plan.description or False,
        "type": plan.type,
        "devices": i18n_format_device_limit(plan.device_limit),
        "traffic": i18n_format_traffic_limit(plan.traffic_limit),
        "period": i18n.get(key, **kw),
        "payment_methods": payment_methods,
        "final_amount": 0,
        "currency": "",
        "only_single_duration": only_single_duration,
        "is_add_devices": False,
    }


@inject
async def confirm_getter(
    dialog_manager: DialogManager,
    i18n: FromDishka[TranslatorRunner],
    payment_gateway_service: FromDishka[PaymentGatewayService],
    **kwargs: Any,
) -> dict[str, Any]:
    adapter = DialogDataAdapter(dialog_manager)
    purchase_type = dialog_manager.dialog_data.get("purchase_type")
    selected_payment_method = dialog_manager.dialog_data["selected_payment_method"]
    payment_gateway = await payment_gateway_service.get_by_type(selected_payment_method)
    result_url = dialog_manager.dialog_data["payment_url"]
    pricing_data = dialog_manager.dialog_data["final_pricing"]
    pricing = PriceDetailsDto.model_validate_json(pricing_data)
    gateways = await payment_gateway_service.filter_active()

    if purchase_type == PurchaseType.ADD_DEVICES:
        addon = adapter.load(DeviceAddonDto)
        if not addon:
            raise ValueError("DeviceAddonDto not found in dialog data")
        if not payment_gateway:
            raise ValueError(f"Not found PaymentGateway by type '{selected_payment_method}'")
        period_key, period_kw = i18n_format_device_limit(addon.device_count)
        devices_str = i18n.get(period_key, **period_kw)
        return {
            "purchase_type": purchase_type,
            "is_add_devices": True,
            "plan": f"+{addon.device_count}",
            "description": False,
            "type": None,
            "devices": devices_str,
            "traffic": i18n_format_traffic_limit(-1),
            "period": f"+{addon.device_count}",
            "payment_method": selected_payment_method,
            "final_amount": pricing.final_amount,
            "discount_percent": pricing.discount_percent,
            "original_amount": pricing.original_amount,
            "currency": payment_gateway.currency.symbol,
            "url": result_url,
            "only_single_gateway": len(gateways) == 1,
            "only_single_duration": False,
            "is_free": pricing.is_free,
        }

    plan = adapter.load(PlanDto)
    if not plan:
        raise ValueError("PlanDto not found in dialog data")
    selected_duration = dialog_manager.dialog_data["selected_duration"]
    only_single_duration = dialog_manager.dialog_data.get("only_single_duration", False)
    is_free = dialog_manager.dialog_data.get("is_free", False)
    duration = plan.get_duration(selected_duration)
    if not duration:
        raise ValueError(f"Duration '{selected_duration}' not found in plan '{plan.name}'")
    if not payment_gateway:
        raise ValueError(f"Not found PaymentGateway by selected type '{selected_payment_method}'")
    key, kw = i18n_format_days(duration.days)
    return {
        "purchase_type": purchase_type,
        "is_add_devices": False,
        "plan": plan.name,
        "description": plan.description or False,
        "type": plan.type,
        "devices": i18n_format_device_limit(plan.device_limit),
        "traffic": i18n_format_traffic_limit(plan.traffic_limit),
        "period": i18n.get(key, **kw),
        "payment_method": selected_payment_method,
        "final_amount": pricing.final_amount,
        "discount_percent": pricing.discount_percent,
        "original_amount": pricing.original_amount,
        "currency": payment_gateway.currency.symbol,
        "url": result_url,
        "only_single_gateway": len(gateways) == 1,
        "only_single_duration": only_single_duration,
        "is_free": is_free,
    }


@inject
async def getter_connect(
    dialog_manager: DialogManager,
    config: AppConfig,
    user: UserDto,
    **kwargs: Any,
) -> dict[str, Any]:
    if not user.current_subscription:
        raise ValueError(f"User '{user.telegram_id}' has no active subscription after purchase")

    return {
        "is_app": config.bot.is_mini_app,
        "url": config.bot.mini_app_url or user.current_subscription.url,
        "connectable": True,
    }


@inject
async def success_payment_getter(
    dialog_manager: DialogManager,
    config: AppConfig,
    user: UserDto,
    i18n: FromDishka[TranslatorRunner],
    **kwargs: Any,
) -> dict[str, Any]:
    start_data = cast(dict[str, Any], dialog_manager.start_data)
    purchase_type: PurchaseType = start_data["purchase_type"]
    subscription = user.current_subscription

    if not subscription:
        raise ValueError(f"User '{user.telegram_id}' has no active subscription after purchase")

    if purchase_type == PurchaseType.ADD_DEVICES:
        device_count = start_data.get("device_count", 0)
        key, kw = i18n_format_device_limit(device_count)
        added_duration = i18n.get(key, **kw)
    else:
        key, kw = i18n_format_days(subscription.plan.duration)
        added_duration = i18n.get(key, **kw)

    return {
        "purchase_type": purchase_type,
        "plan_name": subscription.plan.name,
        "traffic_limit": i18n_format_traffic_limit(subscription.traffic_limit),
        "device_limit": i18n_format_device_limit(subscription.device_limit),
        "expire_time": i18n_format_expire_time(subscription.expire_at),
        "added_duration": added_duration,
        "is_app": config.bot.is_mini_app,
        "url": config.bot.mini_app_url or subscription.url,
        "connectable": True,
    }
