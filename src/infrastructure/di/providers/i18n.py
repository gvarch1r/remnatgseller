from typing import Optional

from dishka import Provider, Scope, provide
from dishka.integrations.aiogram import AiogramMiddlewareData
from fluentogram import TranslatorHub, TranslatorRunner
from fluentogram.storage import FileStorage
from loguru import logger

from src.core.config import AppConfig
from src.core.constants import USER_KEY
from src.core.i18n.translator import normalize_locale_for_hub
from src.infrastructure.database.models.dto import UserDto


class I18nProvider(Provider):
    scope = Scope.APP

    @provide
    def get_hub(self, config: AppConfig) -> TranslatorHub:
        storage = FileStorage(path=str(config.translations_dir) + "/{locale}")
        # FileStorage discovers locales from folder names (en/, ru/). Use lowercase
        # for fallback chain so storage lookup works.
        locales_map: dict[str, tuple[str, ...]] = {}

        for locale_code in config.locales:
            key = normalize_locale_for_hub(locale_code)
            fallback_chain: list[str] = [key]
            if config.default_locale != locale_code:
                fallback_chain.append(normalize_locale_for_hub(config.default_locale))
            locales_map[key] = tuple(fallback_chain)

        default_key = normalize_locale_for_hub(config.default_locale)
        if default_key not in locales_map:
            locales_map[default_key] = (default_key,)

        logger.debug(
            f"Loaded TranslatorHub with locales: {list(locales_map.keys())}, "
            f"default={default_key}"
        )

        return TranslatorHub(locales_map, root_locale=default_key, storage=storage)

    @provide(scope=Scope.REQUEST)
    def get_translator(
        self,
        config: AppConfig,
        hub: TranslatorHub,
        middleware_data: AiogramMiddlewareData,
    ) -> TranslatorRunner:
        user: Optional[UserDto] = middleware_data.get(USER_KEY)

        if user:
            locale = user.language
            if locale not in config.locales:
                locale = config.default_locale
                logger.debug(
                    f"User '{user.telegram_id}' locale '{user.language}' not in locales, "
                    f"using default '{locale}'"
                )
            return hub.get_translator_by_locale(locale=normalize_locale_for_hub(locale))

        else:
            logger.debug(
                f"Translator for anonymous user with default locale={config.default_locale}"
            )
            return hub.get_translator_by_locale(
                locale=normalize_locale_for_hub(config.default_locale)
            )
