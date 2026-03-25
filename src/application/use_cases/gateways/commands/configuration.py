from dataclasses import dataclass
from typing import Any

from loguru import logger
from pydantic import SecretStr

from src.application.common import Interactor
from src.application.common.dao import PaymentGatewayDao
from src.application.common.policy import Permission
from src.application.common.uow import UnitOfWork
from src.application.dto import UserDto
from src.application.dto.payment_gateway import YookassaGatewaySettingsDto
from src.core.enums import YookassaVatCode
from src.core.exceptions import GatewayNotConfiguredError


def _coerce_payment_gateway_field(settings: Any, field_name: str, raw: str) -> Any:
    """Admin UI passes text; numeric and enum fields must match DTO types for API JSON."""
    if field_name == "shop_id":
        return int(raw.strip())
    if field_name == "vat_code":
        code = int(raw.strip())
        if isinstance(settings, YookassaGatewaySettingsDto):
            return YookassaVatCode(code)
        return code
    if field_name == "payment_system_id":
        return int(raw.strip())
    if field_name == "payment_method":
        return int(raw.strip())
    return raw


class MovePaymentGatewayUp(Interactor[int, None]):
    required_permission = Permission.REMNASHOP_GATEWAYS

    def __init__(self, uow: UnitOfWork, gateway_dao: PaymentGatewayDao) -> None:
        self.uow = uow
        self.gateway_dao = gateway_dao

    async def _execute(self, actor: UserDto, gateway_id: int) -> None:
        async with self.uow:
            gateways = await self.gateway_dao.get_all()
            gateways.sort(key=lambda g: g.order_index)

            index = next((i for i, g in enumerate(gateways) if g.id == gateway_id), None)

            if index is None:
                logger.warning(
                    f"Payment gateway with id '{gateway_id}' not found for move operation"
                )
                return

            if index == 0:
                gateway = gateways.pop(0)
                gateways.append(gateway)
                logger.debug(f"Payment gateway '{gateway_id}' moved from top to bottom")
            else:
                gateways[index - 1], gateways[index] = gateways[index], gateways[index - 1]
                logger.debug(f"Payment gateway '{gateway_id}' moved up one position")

            for i, g in enumerate(gateways, start=1):
                if g.order_index != i:
                    g.order_index = i
                    await self.gateway_dao.update(g)

            await self.uow.commit()

        logger.info(f"{actor.log} Moved payment gateway '{gateway_id}' up successfully")


class TogglePaymentGatewayActive(Interactor[int, None]):
    required_permission = Permission.REMNASHOP_GATEWAYS

    def __init__(
        self,
        uow: UnitOfWork,
        gateway_dao: PaymentGatewayDao,
    ) -> None:
        self.uow = uow
        self.gateway_dao = gateway_dao

    async def _execute(self, actor: UserDto, gateway_id: int) -> None:
        async with self.uow:
            gateway = await self.gateway_dao.get_by_id(gateway_id)

            if not gateway:
                raise ValueError(f"Payment gateway with id '{gateway_id}' not found")

            if gateway.settings and not gateway.settings.is_configured:
                raise GatewayNotConfiguredError(f"Gateway '{gateway_id}' is not configured")

            old_status = gateway.is_active
            gateway.is_active = not old_status

            await self.gateway_dao.update(gateway)
            await self.uow.commit()

        logger.info(
            f"{actor.log} Updated payment gateway '{gateway_id}' "
            f"active status from '{old_status}' to '{gateway.is_active}'"
        )


@dataclass(frozen=True)
class UpdatePaymentGatewaySettingsDto:
    gateway_id: int
    field_name: str
    value: str


class UpdatePaymentGatewaySettings(Interactor[UpdatePaymentGatewaySettingsDto, None]):
    required_permission = Permission.REMNASHOP_GATEWAYS

    def __init__(self, uow: UnitOfWork, gateway_dao: PaymentGatewayDao) -> None:
        self.uow = uow
        self.gateway_dao = gateway_dao

    async def _execute(self, actor: UserDto, data: UpdatePaymentGatewaySettingsDto) -> None:
        async with self.uow:
            gateway = await self.gateway_dao.get_by_id(data.gateway_id)

            if not gateway or not gateway.settings:
                raise GatewayNotConfiguredError(f"Gateway '{data.gateway_id}' is not configured")
            try:
                new_value: Any = data.value
                secret_fields = {
                    "api_key",
                    "secret_key",
                    "secret_word_2",
                    "password1",
                    "password2",
                }
                if data.field_name in secret_fields and isinstance(new_value, str):
                    new_value = SecretStr(new_value)
                elif isinstance(new_value, str):
                    new_value = _coerce_payment_gateway_field(
                        gateway.settings,
                        data.field_name,
                        new_value,
                    )

                setattr(gateway.settings, data.field_name, new_value)

                await self.gateway_dao.update(gateway)
                await self.uow.commit()

                logger.info(
                    "ADMIN_AUDIT action=gateway_settings_update "
                    "actor_telegram_id={} gateway_id={} field={}",
                    actor.telegram_id,
                    data.gateway_id,
                    data.field_name,
                )

            except ValueError as e:
                logger.warning(f"{actor.log} Invalid value for field '{data.field_name}': {e}")
                raise
