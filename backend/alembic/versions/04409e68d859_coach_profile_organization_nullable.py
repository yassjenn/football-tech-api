"""coach profile organization nullable

Revision ID: 04409e68d859
Revises: 8eedaa692fd8
Create Date: 2026-04-28 12:53:46.611821

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "04409e68d859"
down_revision: str | Sequence[str] | None = "8eedaa692fd8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "coach_profiles",
        "organization_id",
        existing_type=sa.Integer(),
        nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "coach_profiles",
        "organization_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
