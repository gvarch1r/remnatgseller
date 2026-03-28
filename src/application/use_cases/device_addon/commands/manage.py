from loguru import logger

from src.application.common import Interactor
from src.application.common.dao import DeviceAddonDao
from src.application.common.policy import Permission
from src.application.common.uow import UnitOfWork
from src.application.dto import UserDto


class ToggleDeviceAddonActive(Interactor[int, bool]):
    required_permission = Permission.REMNASHOP_PLAN_EDITOR

    def __init__(
        self,
        uow: UnitOfWork,
        device_addon_dao: DeviceAddonDao,
    ) -> None:
        self.uow = uow
        self.device_addon_dao = device_addon_dao

    async def _execute(self, actor: UserDto, addon_id: int) -> bool:
        async with self.uow:
            new_active = await self.device_addon_dao.toggle_active(addon_id)
            await self.uow.commit()

        logger.info(
            f"{actor.log} Device addon '{addon_id}' active toggled -> {new_active}",
        )
        return new_active
