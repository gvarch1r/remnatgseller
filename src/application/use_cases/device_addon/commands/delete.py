from loguru import logger

from src.application.common import Interactor
from src.application.common.dao import DeviceAddonDao
from src.application.common.policy import Permission
from src.application.common.uow import UnitOfWork
from src.application.dto import UserDto


class DeleteDeviceAddon(Interactor[int, None]):
    required_permission = Permission.REMNASHOP_PLAN_EDITOR

    def __init__(
        self,
        uow: UnitOfWork,
        device_addon_dao: DeviceAddonDao,
    ) -> None:
        self.uow = uow
        self.device_addon_dao = device_addon_dao

    async def _execute(self, actor: UserDto, addon_id: int) -> None:
        async with self.uow:
            deleted = await self.device_addon_dao.delete(addon_id)
            if not deleted:
                raise ValueError(f"Device addon '{addon_id}' not found")
            await self.uow.commit()

        logger.info(f"{actor.log} Deleted device addon id={addon_id}")
