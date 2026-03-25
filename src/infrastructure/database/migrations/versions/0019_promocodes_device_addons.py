from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0019"
down_revision: Union[str, None] = "0018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE purchase_type ADD VALUE IF NOT EXISTS 'ADD_DEVICES'")

    op.create_table(
        "promocodes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "reward_type",
            postgresql.ENUM(name="promocode_reward_type", create_type=False),
            nullable=False,
        ),
        sa.Column("reward", sa.Integer(), nullable=True),
        sa.Column("plan", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("lifetime", sa.Integer(), nullable=True),
        sa.Column("max_activations", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('UTC', now())"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('UTC', now())"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "promocode_activations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("promocode_id", sa.Integer(), nullable=False),
        sa.Column("user_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "activated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('UTC', now())"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["promocode_id"], ["promocodes.id"]),
        sa.ForeignKeyConstraint(["user_telegram_id"], ["users.telegram_id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "device_addons",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("device_count", sa.Integer(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('UTC', now())"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('UTC', now())"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_device_addons_is_active", "device_addons", ["is_active"], unique=False)

    op.create_table(
        "device_addon_prices",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "device_addon_id",
            sa.Integer(),
            sa.ForeignKey("device_addons.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "currency",
            postgresql.ENUM(name="currency", create_type=False),
            nullable=False,
        ),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    conn = op.get_bind()
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
            conn.execute(
                sa.text("""
                    INSERT INTO device_addon_prices (device_addon_id, currency, price)
                    VALUES (:addon_id, 'XTR'::currency, :price)
                """),
                {"addon_id": addon_id, "price": float(device_count * 50)},
            )


def downgrade() -> None:
    op.drop_table("device_addon_prices")
    op.drop_table("device_addons")
    op.drop_table("promocode_activations")
    op.drop_table("promocodes")
