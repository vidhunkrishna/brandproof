"""add human dispute resolution state

Revision ID: e6d4b9c2a701
Revises: f3303cabb192
Create Date: 2026-11-05
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "e6d4b9c2a701"
down_revision: Union[str, Sequence[str], None] = "f3303cabb192"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # SQLAlchemy persists the enum member name for the existing disputestatus type.
    op.execute("ALTER TYPE disputestatus ADD VALUE IF NOT EXISTS 'NEEDS_INFO'")
    op.add_column("disputes", sa.Column("override_verdict", sa.Enum("CORRECT", "CONTRADICTED", "OUTDATED", "UNSUPPORTED", "UNVERIFIABLE", name="findingverdict"), nullable=True))

def downgrade() -> None:
    op.drop_column("disputes", "override_verdict")
    # PostgreSQL enum values cannot be removed safely; the legacy value remains unused on downgrade.
