from typing import Any, Optional
from uuid import UUID


def resolve_squad_uuid(squad: Any) -> Optional[UUID]:
    """UUID сквада из DTO/API; при расхождении версий панели и remnapy допускает dict и поле id."""
    try:
        raw = getattr(squad, "uuid", None)
        if raw is not None:
            return raw if isinstance(raw, UUID) else UUID(str(raw))
        if isinstance(squad, dict):
            for key in ("uuid", "id", "squadUuid", "squad_uuid"):
                val = squad.get(key)
                if val is not None:
                    return UUID(str(val))
    except (TypeError, ValueError):
        return None
    return None
