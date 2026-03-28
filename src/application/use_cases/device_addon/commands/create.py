from loguru import logger

from src.application.common import Interactor
from src.application.common.dao import DeviceAddonDao
from src.application.common.policy import Permission
from src.application.common.uow import UnitOfWork
from src.application.dto import CreateDeviceAddonDto, DeviceAddonDto, UserDto


class CreateDeviceAddon(Interactor[CreateDeviceAddonDto, DeviceAddonDto]):
    required_permission = Permission.REMNASHOP_PLAN_EDITOR

    def __init__(
        self,
        uow: UnitOfWork,
        device_addon_dao: DeviceAddonDao,
    ) -> None:
        self.uow = uow
        self.device_addon_dao = device_addon_dao

    async def _execute(self, actor: UserDto, data: CreateDeviceAddonDto) -> DeviceAddonDto:
        if data.device_count < 1:
            raise ValueError("device_count must be >= 1")
        if not data.prices:
            raise ValueError("prices must not be empty")
        for price in data.prices.values():
            if price <= 0:
                raise ValueError("price must be positive")

        async with self.uow:
            dto = await self.device_addon_dao.create(data.device_count, data.prices)
            await self.uow.commit()

        logger.info(
            f"{actor.log} Device addon created id={dto.id} devices={data.device_count}",
        )
        return dto
