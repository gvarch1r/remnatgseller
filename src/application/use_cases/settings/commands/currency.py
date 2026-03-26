from dataclasses import dataclass
from decimal import ROUND_DOWN, Decimal, InvalidOperation
from typing import Literal

from loguru import logger

from src.application.common import Interactor
from src.application.common.dao import SettingsDao
from src.application.common.policy import Permission
from src.application.common.uow import UnitOfWork
from src.application.dto import UserDto
from src.core.enums import Currency


class UpdateDefaultCurrency(Interactor[Currency, None]):
    required_permission = Permission.SETTINGS_CURRENCY

    def __init__(self, uow: UnitOfWork, settings_dao: SettingsDao) -> None:
        self.uow = uow
        self.settings_dao = settings_dao

    async def _execute(self, actor: UserDto, currency: Currency) -> None:
        async with self.uow:
            settings = await self.settings_dao.get()
            old_currency = settings.default_currency

            if old_currency == currency:
                logger.debug(f"Default currency is already set to '{currency}'")
                return

            settings.default_currency = currency
            await self.settings_dao.update(settings)
            await self.uow.commit()

        logger.info(f"{actor.log} Updated default currency from '{old_currency}' to '{currency}'")


@dataclass(frozen=True)
class UpdateCurrencyRatesFieldDto:
    field: Literal["stars_per_usd", "usd_rub_override"]
    value: str


class UpdateCurrencyRatesField(Interactor[UpdateCurrencyRatesFieldDto, None]):
    required_permission = Permission.SETTINGS_CURRENCY

    def __init__(self, uow: UnitOfWork, settings_dao: SettingsDao) -> None:
        self.uow = uow
        self.settings_dao = settings_dao

    async def _execute(self, actor: UserDto, data: UpdateCurrencyRatesFieldDto) -> None:
        raw = (data.value or "").strip()
        reset_tokens = {"", "-", "сброс", "reset"}

        async with self.uow:
            settings = await self.settings_dao.get()

            if data.field == "stars_per_usd":
                try:
                    stars = Decimal(raw)
                except InvalidOperation:
                    logger.warning(f"{actor.log} Invalid stars_per_usd: '{raw}'")
                    raise ValueError() from None
                stars_int = stars.to_integral_value(rounding=ROUND_DOWN)
                if stars_int < 1:
                    raise ValueError()
                settings.currency_rates.stars_per_usd = stars_int

            elif data.field == "usd_rub_override":
                if raw.lower() in reset_tokens:
                    settings.currency_rates.usd_rub_override = None
                else:
                    try:
                        rate = Decimal(raw.replace(",", "."))
                    except InvalidOperation:
                        logger.warning(f"{actor.log} Invalid usd_rub_override: '{raw}'")
                        raise ValueError() from None
                    if rate <= 0:
                        raise ValueError()
                    settings.currency_rates.usd_rub_override = rate
            else:
                raise ValueError()

            await self.settings_dao.update(settings)
            await self.uow.commit()

        logger.info(f"{actor.log} Updated currency_rates.{data.field}")
