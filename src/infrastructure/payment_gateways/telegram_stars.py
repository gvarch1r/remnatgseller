import uuid
from decimal import Decimal
from uuid import UUID

from aiogram.types import LabeledPrice
from fastapi import Request
from loguru import logger

from src.application.dto import PaymentResultDto
from src.core.enums import Currency, TransactionStatus

from .base import BasePaymentGateway


# https://core.telegram.org/api/stars/
class TelegramStarsGateway(BasePaymentGateway):
    async def handle_create_payment(self, amount: Decimal, details: str) -> PaymentResultDto:
        payment_id = uuid.uuid4()
        currency_code = (
            self.data.currency.value
            if isinstance(self.data.currency, Currency)
            else str(self.data.currency)
        )
        text = details.strip()
        title = (text[:32] if text else "VPN")[:32]
        description = (text[:255] if text else title)[:255]
        # Single line item for XTR: label is shown to the user, not the ISO currency code.
        item_label = (text[:128] if text else title)[:128]
        prices = [LabeledPrice(label=item_label, amount=int(amount))]

        try:
            payment_url = await self.bot.create_invoice_link(
                title=title,
                description=description,
                payload=str(payment_id),
                currency=currency_code,
                prices=prices,
                provider_token="",
            )

            return PaymentResultDto(id=payment_id, url=payment_url)

        except Exception as e:
            logger.exception(f"An unexpected error occurred while creating payment: {e}")
            raise

    async def handle_webhook(self, request: Request) -> tuple[UUID, TransactionStatus]:
        raise NotImplementedError()
