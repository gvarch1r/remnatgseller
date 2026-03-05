"""Add device addon prices for USD and RUB (migration 0019 only added XTR)."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0020"
down_revision: Union[str, None] = "0019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # Если device_addons пустая — сидируем как в 0019 (на случай пропущенной миграции)
    result = conn.execute(sa.text("SELECT 1 FROM device_addons LIMIT 1"))
    if result.fetchone() is None:
        for device_count, order_index in [(1, 1), (2, 2), (3, 3)]:
            r = conn.execute(
                sa.text("""
                    INSERT INTO device_addons (device_count, order_index, is_active)
                    VALUES (:dc, :oi, true)
                    RETURNING id
                """),
                {"dc": device_count, "oi": order_index},
            )
            addon_id = r.scalar()
            for currency, price_per_device in [("XTR", 50), ("USD", 0.5), ("RUB", 50)]:
                conn.execute(
                    sa.text("""
                        INSERT INTO device_addon_prices (device_addon_id, currency, price)
                        VALUES (:addon_id, :currency::currency, :price)
                    """),
                    {
                        "addon_id": addon_id,
                        "currency": currency,
                        "price": float(device_count * price_per_device),
                    },
                )
        return

    # Добавить USD и RUB для существующих addons
    for currency, price_per_device in [("USD", 0.5), ("RUB", 50)]:
        conn.execute(
            sa.text("""
                INSERT INTO device_addon_prices (device_addon_id, currency, price)
                SELECT da.id, :currency::currency, da.device_count * :price
                FROM device_addons da
                WHERE da.is_active = true
                  AND NOT EXISTS (
                    SELECT 1 FROM device_addon_prices dap
                    WHERE dap.device_addon_id = da.id AND dap.currency = :currency::currency
                  )
            """),
            {"currency": currency, "price": float(price_per_device)},
        )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("""
            DELETE FROM device_addon_prices
            WHERE currency IN ('USD', 'RUB')
        """)
    )
