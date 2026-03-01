from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0018"
down_revision: Union[str, None] = "0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    audit_action_type_enum = sa.Enum(
        "REGISTERED",
        "SUBSCRIPTION_CREATED",
        "SUBSCRIPTION_UPDATED",
        "SUBSCRIPTION_DELETED",
        "ROLE_CHANGED",
        "BLOCKED",
        "UNBLOCKED",
        "DISCOUNT_CHANGED",
        "POINTS_CHANGED",
        "PURCHASE_COMPLETED",
        "PROMOCODE_ACTIVATED",
        "REFERRAL_ATTACHED",
        "DEVICE_ADDED",
        "DEVICE_REMOVED",
        "SYNC_FROM_REMNAWAVE",
        "SYNC_FROM_REMNATGSELLER",
        "GIVE_SUBSCRIPTION",
        "GIVE_ACCESS",
        "MESSAGE_SENT",
        name="audit_action_type",
    )
    audit_action_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("actor_telegram_id", sa.BigInteger(), nullable=True),
        sa.Column("action_type", audit_action_type_enum, nullable=False),
        sa.Column("details", sa.Text(), nullable=False, server_default=""),
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
    op.create_index(
        "ix_audit_logs_user_telegram_id",
        "audit_logs",
        ["user_telegram_id"],
        unique=False,
    )
    op.create_index(
        "ix_audit_logs_created_at",
        "audit_logs",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_telegram_id", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.execute("DROP TYPE IF EXISTS audit_action_type")
