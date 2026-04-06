"""seed admin user

Revision ID: a93240b89c29
Revises: c5922eaddc5f
Create Date: 2026-03-02 06:41:46.191833

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a93240b89c29'
down_revision: Union[str, Sequence[str], None] = 'c5922eaddc5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
