"""tz 3.2: oauth social_accounts + partition login_history by device type

Revision ID: c1c4f122c157
Revises: 7fafe13831a2
Create Date: 2026-03-02 08:55:04

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision: str = "c1c4f122c157"
down_revision: Union[str, Sequence[str], None] = "7fafe13831a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_partitioned(conn) -> bool:
    q = sa.text(
        """
        SELECT EXISTS(
            SELECT 1
            FROM pg_partitioned_table pt
            JOIN pg_class c ON c.oid = pt.partrelid
            WHERE c.relname = 'login_history'
        );
        """
    )
    return bool(conn.execute(q).scalar())


def upgrade() -> None:
    conn = op.get_bind()

    # social_accounts
    op.create_table(
        "social_accounts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("social_id", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("provider", "social_id", name="uq_social_provider_social_id"),
    )

    # partition login_history by LIST(user_device_type)
    if not _is_partitioned(conn):
        op.execute('ALTER TABLE login_history RENAME TO login_history_old;')

        op.execute(
            """
            CREATE TABLE login_history (
                id uuid NOT NULL,
                user_device_type text NOT NULL DEFAULT 'web',
                user_id uuid NOT NULL,
                user_agent varchar(512),
                ip varchar(50),
                success boolean DEFAULT true,
                created_at timestamp,
                PRIMARY KEY (id, user_device_type),
                CONSTRAINT fk_login_history_user_id_users
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            ) PARTITION BY LIST (user_device_type);
            """
        )

        op.execute("CREATE TABLE login_history_web PARTITION OF login_history FOR VALUES IN ('web');")
        op.execute("CREATE TABLE login_history_mobile PARTITION OF login_history FOR VALUES IN ('mobile');")
        op.execute("CREATE TABLE login_history_smart PARTITION OF login_history FOR VALUES IN ('smart');")
        op.execute("CREATE TABLE login_history_default PARTITION OF login_history DEFAULT;")

        op.execute(
            """
            INSERT INTO login_history (id, user_device_type, user_id, user_agent, ip, success, created_at)
            SELECT id, 'web', user_id, user_agent, ip, success, created_at
            FROM login_history_old;
            """
        )

        op.execute("DROP TABLE login_history_old;")


def downgrade() -> None:
    conn = op.get_bind()

    op.drop_table("social_accounts")

    if _is_partitioned(conn):
        op.execute("ALTER TABLE login_history RENAME TO login_history_part;")

        op.execute(
            """
            CREATE TABLE login_history (
                id uuid PRIMARY KEY,
                user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                user_agent varchar(512),
                ip varchar(50),
                success boolean DEFAULT true,
                created_at timestamp
            );
            """
        )

        op.execute(
            """
            INSERT INTO login_history (id, user_id, user_agent, ip, success, created_at)
            SELECT id, user_id, user_agent, ip, success, created_at
            FROM login_history_part;
            """
        )

        op.execute("DROP TABLE login_history_part CASCADE;")
