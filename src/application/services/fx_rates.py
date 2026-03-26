from decimal import Decimal

import httpx
from loguru import logger


class ExchangeRateFetchError(Exception):
    """Не удалось получить курс USD/RUB (сеть, формат ответа ЦБ)."""


class CbrUsdRubProvider:
    """Курс USD→RUB (сколько рублей за 1 доллар) с daily_json ЦБ (неофициальное зеркало)."""

    _URL = "https://www.cbr-xml-daily.ru/daily_json.js"

    async def get_rub_per_usd(self) -> Decimal:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self._URL)
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError) as e:
            logger.warning(f"CBR daily_json request failed: {e!r}")
            raise ExchangeRateFetchError() from e

        try:
            value = data["Valute"]["USD"]["Value"]
            rub_per_usd = Decimal(str(value))
        except (KeyError, TypeError, ArithmeticError) as e:
            logger.warning(f"Unexpected CBR JSON shape: {e!r}")
            raise ExchangeRateFetchError() from e

        if rub_per_usd <= 0:
            raise ExchangeRateFetchError()

        logger.debug(f"CBR USD rate: 1 USD = {rub_per_usd} RUB")
        return rub_per_usd
