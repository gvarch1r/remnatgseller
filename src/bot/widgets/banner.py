import functools
from pathlib import Path
from typing import Any, Optional

from aiogram.types import ContentType
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment
from aiogram_dialog.widgets.common import Whenable
from aiogram_dialog.widgets.media import StaticMedia
from loguru import logger

from src.core.config import AppConfig
from src.core.constants import CONFIG_KEY, USER_KEY
from src.core.enums import BannerFormat, BannerName, Locale
from src.infrastructure.database.models.dto import UserDto


def _locale_banner_subdirs(banners_dir: Path, loc: Locale) -> list[Path]:
    """Try lowercase first (ru/en — как в translations), then original casing (RU/EN)."""
    raw = str(loc)
    lowered = raw.lower()
    out: list[Path] = []
    for sub in (lowered, raw):
        candidate = banners_dir / sub
        if candidate.is_dir() and candidate not in out:
            out.append(candidate)
    return out


def _banner_filename_patterns(name: BannerName) -> list[str]:
    """Имена файлов в нижнем регистре (menu.jpg, about_us.png); затем вариант как в enum — для совместимости."""
    raw = name.value
    lowered = raw.lower()
    patterns = [f"{lowered}.{{format}}"]
    if raw != lowered:
        patterns.append(f"{raw}.{{format}}")
    return patterns


def _patterns_with_default_fallback(name: BannerName) -> list[str]:
    patterns = _banner_filename_patterns(name)
    if name != BannerName.DEFAULT:
        patterns.extend(_banner_filename_patterns(BannerName.DEFAULT))
    return patterns


def _ordered_locale_banner_dirs(
    banners_dir: Path,
    locale: Locale,
    default_locale: Locale,
) -> list[Path]:
    seen: set[Path] = set()
    ordered: list[Path] = []
    for loc in (locale, default_locale):
        for p in _locale_banner_subdirs(banners_dir, loc):
            if p not in seen:
                seen.add(p)
                ordered.append(p)
    return ordered


@functools.lru_cache(maxsize=None)
def get_banner(
    banners_dir: Path,
    name: BannerName,
    locale: Locale,
    default_locale: Locale,
) -> tuple[Path, ContentType]:
    def find_in_dirs(dirs: list[Path], filenames: list[str]) -> tuple[Path, ContentType] | None:
        for directory in dirs:
            if not directory.exists():
                continue
            for format in BannerFormat:
                for pattern in filenames:
                    filename = pattern.format(format=format)
                    candidate = directory / filename
                    if candidate.exists():
                        return candidate, format.content_type
        return None

    locale_dirs = _ordered_locale_banner_dirs(banners_dir, locale, default_locale)

    result = find_in_dirs(locale_dirs, filenames=_patterns_with_default_fallback(name))
    if result:
        return result

    logger.warning(f"Banner '{name}' not found in locales '{locale}' or '{default_locale}'")

    result = find_in_dirs([banners_dir], filenames=_banner_filename_patterns(BannerName.DEFAULT))
    if result:
        return result

    raise FileNotFoundError("Default banner not found in any locale or globally")


class Banner(StaticMedia):
    def __init__(self, name: BannerName) -> None:
        self.banner_name = name

        def _is_use_banners(
            data: dict[str, Any],
            widget: Whenable,
            dialog_manager: DialogManager,
        ) -> bool:
            config: AppConfig = dialog_manager.middleware_data[CONFIG_KEY]
            return config.bot.use_banners

        super().__init__(path="path", url=None, type=ContentType.UNKNOWN, when=_is_use_banners)

    async def _render_media(self, data: dict, manager: DialogManager) -> Optional[MediaAttachment]:
        user: UserDto = manager.middleware_data[USER_KEY]
        config: AppConfig = manager.middleware_data[CONFIG_KEY]

        banner_path, banner_content_type = get_banner(
            banners_dir=config.banners_dir,
            name=self.banner_name,
            locale=user.language,
            default_locale=config.default_locale,
        )

        return MediaAttachment(
            type=banner_content_type,
            url=None,
            path=banner_path,
            use_pipe=self.use_pipe,
            **self.media_params,
        )
