"""convert_overall_verdict_to_revisionverdict_enum

Revision ID: 82a2d7e1e698
Revises: f9ac8e2d5a81
Create Date: 2026-11-05 17:55:22.217905

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '82a2d7e1e698'
down_revision: Union[str, Sequence[str], None] = 'f9ac8e2d5a81'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ENUM_NAME = 'revisionverdict'
ENUM_VALUES = (
    'CORRECT',
    'CONTRADICTED',
    'OUTDATED',
    'UNSUPPORTED',
    'UNVERIFIABLE',
    'MIXED',
    'NEEDS_REVIEW',
)


def upgrade() -> None:
    """Upgrade schema to use revisionverdict enum supporting MIXED and NEEDS_REVIEW."""
    bind = op.get_bind()

    # 1. Create PostgreSQL enum type
    revision_verdict_enum = sa.Enum(*ENUM_VALUES, name=ENUM_NAME)
    revision_verdict_enum.create(bind, checkfirst=True)

    # 2. Sanitize any existing rows with legacy 'PENDING' to 'NEEDS_REVIEW'
    op.execute(
        f"UPDATE submission_revisions SET overall_verdict = 'NEEDS_REVIEW' "
        f"WHERE overall_verdict NOT IN {ENUM_VALUES}"
    )

    # 3. Alter column to use PostgreSQL enum with explicit cast
    op.execute(
        f"ALTER TABLE submission_revisions "
        f"ALTER COLUMN overall_verdict TYPE {ENUM_NAME} "
        f"USING overall_verdict::{ENUM_NAME}"
    )


def downgrade() -> None:
    """Downgrade schema back to VARCHAR(50)."""
    bind = op.get_bind()

    # 1. Alter column back to VARCHAR(50)
    op.execute(
        "ALTER TABLE submission_revisions "
        "ALTER COLUMN overall_verdict TYPE VARCHAR(50) "
        "USING overall_verdict::VARCHAR(50)"
    )

    # 2. Drop PostgreSQL enum type
    sa.Enum(name=ENUM_NAME).drop(bind, checkfirst=True)
