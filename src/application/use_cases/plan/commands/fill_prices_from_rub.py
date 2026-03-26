from dataclasses import dataclass
from decimal import ROUND_DOWN

from loguru import logger

from src.application.common import Interactor
from src.application.common.dao import SettingsDao
from src.application.common.policy import Permission
from src.application.dto import PlanDto, UserDto
from src.application.services.fx_rates import CbrUsdRubProvider
from src.application.services.pricing import PricingService
from src.core.enums import Currency


@dataclass(frozen=True)
class FillPlanPricesFromRubDto:
    plan: PlanDto
    duration: int
    input_rub: str


class FillPlanPricesFromRub(Interactor[FillPlanPricesFromRubDto, PlanDto]):
    required_permission = Permission.REMNASHOP_PLAN_EDITOR

    def __init__(
        self,
        pricing_service: PricingService,
        settings_dao: SettingsDao,
        cbr: CbrUsdRubProvider,
    ) -> None:
        self._pricing = pricing_service
        self._settings_dao = settings_dao
        self._cbr = cbr

    async def _execute(self, actor: UserDto, data: FillPlanPricesFromRubDto) -> PlanDto:
        try:
            rub = self._pricing.parse_price(data.input_rub, Currency.RUB)
        except ValueError:
            logger.warning(f"{actor.log} Invalid RUB amount for fill-from-rub: '{data.input_rub}'")
            raise

        if rub <= 0:
            raise ValueError("RUB price must be positive")

        settings = await self._settings_dao.get()
        rates = settings.currency_rates

        if rates.usd_rub_override is not None:
            rub_per_usd = rates.usd_rub_override
            if rub_per_usd <= 0:
                raise ValueError("usd_rub_override in settings must be positive")
        else:
            rub_per_usd = await self._cbr.get_rub_per_usd()

        usd_raw = rub / rub_per_usd
        usd = self._pricing.apply_currency_rules(usd_raw, Currency.USD)

        xtr_from_usd = (usd * rates.stars_per_usd).to_integral_value(rounding=ROUND_DOWN)
        xtr = self._pricing.apply_currency_rules(xtr_from_usd, Currency.XTR)

        for duration in data.plan.durations:
            if duration.days != data.duration:
                continue
            for price_dto in duration.prices:
                if price_dto.currency == Currency.RUB:
                    price_dto.price = rub
                elif price_dto.currency == Currency.USD:
                    price_dto.price = usd
                elif price_dto.currency == Currency.XTR:
                    price_dto.price = xtr

            logger.info(
                f"{actor.log} Filled plan prices from RUB={rub} for duration {data.duration}d "
                f"→ USD={usd}, XTR={xtr} (rub_per_usd={rub_per_usd})"
            )
            return data.plan

        logger.warning(f"{actor.log} Duration '{data.duration}' not found for fill-from-rub")
        raise ValueError("Target duration not found in plan")
