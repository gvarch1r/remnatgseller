import base64
import hashlib
import json
import uuid
from decimal import Decimal
from hmac import compare_digest
from typing import Any
from uuid import UUID

import orjson
from aiogram import Bot
from fastapi import Request
from httpx import AsyncClient, HTTPStatusError
from loguru import logger

from src.application.dto import PaymentGatewayDto, PaymentResultDto
from src.application.dto.payment_gateway import (
    CryptomusGatewaySettingsDto,
    HeleketGatewaySettingsDto,
)
from src.core.config import AppConfig
from src.core.enums import TransactionStatus

from .base import BasePaymentGateway
from .exceptions import PaymentWebhookIgnored


# https://doc.cryptomus.com/
class CryptomusGateway(BasePaymentGateway):
    _client: AsyncClient

    API_BASE = "https://api.cryptomus.com/"

    NETWORKS = ["91.227.144.54/32"]

    # Cryptomus invoice lifetime: 300–43200 seconds
    _INVOICE_LIFETIME_SEC = 1800

    def __init__(self, gateway: PaymentGatewayDto, bot: Bot, config: AppConfig) -> None:
        super().__init__(gateway, bot, config)

        if not isinstance(
            self.data.settings, (CryptomusGatewaySettingsDto, HeleketGatewaySettingsDto)
        ):
            raise TypeError(
                f"Invalid settings type: expected {CryptomusGatewaySettingsDto.__name__} "
                f"or {HeleketGatewaySettingsDto.__name__}, got {type(self.data.settings).__name__}"
            )

        self._client = self._make_client(
            base_url=self.API_BASE,
            headers={"merchant": str(self.data.settings.merchant_id)},  # type: ignore[dict-item]
        )

    @staticmethod
    def _serialize_cryptomus_json(data: dict[str, Any]) -> str:
        """
        Cryptomus signs the same JSON as PHP json_encode (slashes escaped in strings).
        See https://doc.cryptomus.com/merchant-api/payments/webhook
        """
        raw = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
        return raw.replace("/", r"\/")

    async def handle_create_payment(self, amount: Decimal, details: str) -> PaymentResultDto:
        order_id = str(uuid.uuid4())
        payload = await self._create_payment_payload(str(amount), order_id, details)
        body_str = self._serialize_cryptomus_json(payload)
        headers = {
            "sign": self._generate_signature(body_str),
            "Content-Type": "application/json",
        }
        logger.debug(f"Creating Cryptomus payment, order_id={order_id}")

        try:
            response = await self._client.post(
                "v1/payment",
                content=body_str.encode("utf-8"),
                headers=headers,
            )
            response.raise_for_status()
            parsed = orjson.loads(response.content)
            if parsed.get("state") != 0:
                msg = parsed.get("message") or parsed.get("errors") or parsed
                logger.error(f"Cryptomus API rejected invoice: {msg}")
                raise ValueError(f"Cryptomus API error: {msg}")

            data = parsed.get("result") or {}
            return self._get_payment_data(data)

        except HTTPStatusError as e:
            logger.error(
                f"HTTP error creating payment. "
                f"Status: '{e.response.status_code}', Body: {e.response.text}"
            )
            raise
        except (KeyError, orjson.JSONDecodeError) as e:
            logger.error(f"Failed to parse response. Error: {e}")
            raise
        except Exception as e:
            logger.exception(f"An unexpected error occurred while creating payment: {e}")
            raise

    async def handle_webhook(self, request: Request) -> tuple[UUID, TransactionStatus]:
        logger.debug(f"Received {self.__class__.__name__} webhook request")
        webhook_data = await self._get_webhook_data(request)

        if not self._verify_webhook(request, webhook_data):
            raise PermissionError("Webhook verification failed")

        payment_id_str = webhook_data.get("order_id")
        if not payment_id_str:
            raise ValueError("Required field 'order_id' is missing")

        status = webhook_data.get("status")
        payment_id = self._parse_order_id(str(payment_id_str))

        match status:
            case "paid" | "paid_over":
                return payment_id, TransactionStatus.COMPLETED
            case "cancel" | "fail" | "wrong_amount" | "system_fail" | "refund_fail":
                return payment_id, TransactionStatus.CANCELED
            case "refund_paid":
                return payment_id, TransactionStatus.CANCELED
            case "confirm_check" | "refund_process":
                raise PaymentWebhookIgnored()
            case _:
                logger.warning(f"Cryptomus webhook unknown status '{status}', ignoring")
                raise PaymentWebhookIgnored()

    async def _create_payment_payload(self, amount: str, order_id: str, details: str) -> dict[str, Any]:
        lifetime = max(300, min(self._INVOICE_LIFETIME_SEC, 43200))
        payload: dict[str, Any] = {
            "amount": amount,
            "currency": str(self.data.currency),
            "order_id": order_id,
            "url_return": await self._get_bot_redirect_url(),
            "url_success": await self._get_bot_redirect_url(),
            "url_callback": self.config.get_webhook(self.data.type),
            "lifetime": lifetime,
            "is_payment_multiple": False,
        }
        if details.strip():
            payload["additional_data"] = details.strip()[:255]
        return payload

    def _generate_signature(self, data: str) -> str:
        base64_encoded = base64.b64encode(data.encode("utf-8")).decode()
        raw_string = f"{base64_encoded}{self.data.settings.api_key.get_secret_value()}"  # type: ignore[union-attr]
        return hashlib.md5(raw_string.encode()).hexdigest()

    def _get_payment_data(self, data: dict[str, Any]) -> PaymentResultDto:
        payment_id_str = data.get("order_id")
        if not payment_id_str:
            raise KeyError("Invalid response from API: missing 'order_id'")

        payment_url = data.get("url")
        if not payment_url:
            raise KeyError("Invalid response from API: missing 'url'")

        return PaymentResultDto(id=self._parse_order_id(str(payment_id_str)), url=str(payment_url))

    @staticmethod
    def _parse_order_id(raw: str) -> UUID:
        """Cryptomus may send order_id as UUID with or without hyphens."""
        s = raw.strip()
        if len(s) == 32 and "-" not in s:
            return UUID(hex=s)
        return UUID(s)

    def _verify_webhook(self, request: Request, data: dict[str, Any]) -> bool:
        ip = self._get_ip(request.headers)

        if not self._is_ip_trusted(ip):
            logger.critical(f"Webhook received from untrusted IP: '{ip}'")
            return False

        sign = data.get("sign")
        if not sign:
            logger.warning("Cryptomus webhook missing signature")
            return False

        payload = {k: v for k, v in data.items() if k != "sign"}
        json_data = self._serialize_cryptomus_json(payload)
        hash_value = self._generate_signature(json_data)

        if not compare_digest(hash_value, str(sign)):
            logger.warning("Invalid Cryptomus webhook signature")
            return False

        return True
