from dataclasses import dataclass
from typing import Any, Optional

from loguru import logger

from src.application.common import Interactor, Remnawave
from src.application.common.dao import PromocodeDao, SubscriptionDao, UserDao
from src.application.common.policy import Permission
from src.application.common.uow import UnitOfWork
from src.application.dto import PlanSnapshotDto, SubscriptionDto, UserDto
from src.core.enums import PromocodeRewardType, SubscriptionStatus
from src.core.types import RemnaUserDto


@dataclass(frozen=True)
class ActivatePromocodeDto:
    code: str


@dataclass(frozen=True)
class ActivatePromocodeResultDto:
    success: bool
    i18n_key: str
    i18n_kwargs: Optional[dict[str, Any]] = None


def _subscription_from_remna(remna_user: RemnaUserDto, plan: PlanSnapshotDto) -> SubscriptionDto:
    return SubscriptionDto(
        user_remna_id=remna_user.uuid,
        status=SubscriptionStatus(remna_user.status),
        traffic_limit=plan.traffic_limit,
        device_limit=plan.device_limit,
        traffic_limit_strategy=plan.traffic_limit_strategy,
        tag=plan.tag,
        internal_squads=plan.internal_squads,
        external_squad=plan.external_squad,
        expire_at=remna_user.expire_at,
        url=remna_user.subscription_url,  # type: ignore[arg-type]
        plan_snapshot=plan,
    )


class ActivatePromocode(Interactor[ActivatePromocodeDto, ActivatePromocodeResultDto]):
    required_permission = Permission.PUBLIC

    def __init__(
        self,
        uow: UnitOfWork,
        promocode_dao: PromocodeDao,
        user_dao: UserDao,
        subscription_dao: SubscriptionDao,
        remnawave: Remnawave,
    ) -> None:
        self.uow = uow
        self.promocode_dao = promocode_dao
        self.user_dao = user_dao
        self.subscription_dao = subscription_dao
        self.remnawave = remnawave

    async def _execute(
        self, actor: UserDto, data: ActivatePromocodeDto
    ) -> ActivatePromocodeResultDto:
        code_clean = (data.code or "").strip().upper()
        if not code_clean:
            return ActivatePromocodeResultDto(False, "ntf-promocode.invalid-code", None)

        async with self.uow:
            promocode = await self.promocode_dao.get_by_code(code_clean)
            if not promocode or not promocode.is_active:
                logger.info(f"{actor.log} Promocode '{code_clean}' not found or inactive")
                return ActivatePromocodeResultDto(False, "ntf-promocode.not-found", None)

            if promocode.is_expired:
                return ActivatePromocodeResultDto(False, "ntf-promocode.expired", None)

            pid = promocode.id
            if pid is None:
                return ActivatePromocodeResultDto(False, "ntf-promocode.not-found", None)

            activations_count = await self.promocode_dao.count_activations(pid)
            if promocode.max_activations is not None and promocode.max_activations >= 0:
                if activations_count >= promocode.max_activations:
                    return ActivatePromocodeResultDto(False, "ntf-promocode.depleted", None)

            if await self.promocode_dao.has_user_activated(actor.telegram_id, pid):
                return ActivatePromocodeResultDto(False, "ntf-promocode.already-activated", None)

            user = await self.user_dao.get_by_telegram_id(actor.telegram_id)
            if not user:
                return ActivatePromocodeResultDto(False, "ntf-promocode.not-found", None)

            if promocode.reward_type == PromocodeRewardType.PERSONAL_DISCOUNT:
                reward_percent = promocode.reward or 0
                new_discount = max(user.personal_discount or 0, reward_percent)
                await self.promocode_dao.create_activation(pid, user.telegram_id)
                user.personal_discount = new_discount
                await self.user_dao.update(user)
                await self.uow.commit()
                logger.info(f"{actor.log} Activated promocode '{promocode.code}' (personal discount)")
                return ActivatePromocodeResultDto(
                    True,
                    "ntf-promocode.activated-success",
                    {"percent": reward_percent},
                )

            if promocode.reward_type == PromocodeRewardType.PURCHASE_DISCOUNT:
                reward_percent = promocode.reward or 0
                new_discount = max(user.purchase_discount or 0, reward_percent)
                await self.promocode_dao.create_activation(pid, user.telegram_id)
                user.purchase_discount = new_discount
                await self.user_dao.update(user)
                await self.uow.commit()
                logger.info(f"{actor.log} Activated promocode '{promocode.code}' (purchase discount)")
                return ActivatePromocodeResultDto(
                    True,
                    "ntf-promocode.activated-success",
                    {"percent": reward_percent},
                )

            if promocode.reward_type == PromocodeRewardType.SUBSCRIPTION:
                plan_snap = promocode.plan
                if not plan_snap:
                    return ActivatePromocodeResultDto(
                        False,
                        "ntf-promocode.subscription-plan-required",
                        None,
                    )

                try:
                    current_sub = await self.subscription_dao.get_current(user.telegram_id)
                    if current_sub:
                        await self.subscription_dao.update_status(
                            subscription_id=current_sub.id,  # type: ignore[arg-type]
                            status=SubscriptionStatus.DISABLED,
                        )
                        remna_user = await self.remnawave.update_user(
                            user=user,
                            uuid=current_sub.user_remna_id,
                            plan=plan_snap,
                            reset_traffic=True,
                        )
                    else:
                        remna_user = await self.remnawave.create_user(user, plan=plan_snap)

                    new_sub = _subscription_from_remna(remna_user, plan_snap)
                    await self.subscription_dao.create(new_sub, user.telegram_id)
                    await self.user_dao.set_trial_available(user.telegram_id, False)
                    await self.promocode_dao.create_activation(pid, user.telegram_id)
                    await self.uow.commit()
                except Exception as exc:
                    logger.exception(
                        f"{actor.log} Subscription promocode '{promocode.code}' failed: {exc}"
                    )
                    return ActivatePromocodeResultDto(
                        False,
                        "ntf-promocode.subscription-activate-failed",
                        None,
                    )

                logger.info(f"{actor.log} Activated promocode '{promocode.code}' (subscription)")
                return ActivatePromocodeResultDto(
                    True,
                    "ntf-promocode.subscription-activated-success",
                    {"plan_name": plan_snap.name},
                )

            return ActivatePromocodeResultDto(False, "ntf-promocode.unsupported-type", None)
