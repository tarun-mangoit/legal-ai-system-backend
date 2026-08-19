"""add new case statuses

Revision ID: 199f3fb2f8c0
Revises: b9bf70d61cb5
Create Date: 2026-08-13 19:41:52.404103

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '199f3fb2f8c0'
down_revision: Union[str, None] = 'b9bf70d61cb5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE case_status_enum ADD VALUE IF NOT EXISTS 'PENDING_ASSIGNMENT'")
        op.execute("ALTER TYPE case_status_enum ADD VALUE IF NOT EXISTS 'ADVOCATE_ASSIGNED'")
        op.execute("ALTER TYPE case_status_enum ADD VALUE IF NOT EXISTS 'IN_PROGRESS'")
        op.execute("ALTER TYPE case_status_enum ADD VALUE IF NOT EXISTS 'DOCUMENTS_UNDER_REVIEW'")
        op.execute("ALTER TYPE case_status_enum ADD VALUE IF NOT EXISTS 'INFORMATION_REQUIRED'")
        op.execute("ALTER TYPE case_status_enum ADD VALUE IF NOT EXISTS 'LEGAL_REVIEW'")
        op.execute("ALTER TYPE case_status_enum ADD VALUE IF NOT EXISTS 'LEGAL_OPINION_DRAFT'")
        op.execute("ALTER TYPE case_status_enum ADD VALUE IF NOT EXISTS 'LEGAL_OPINION_SUBMITTED'")
        op.execute("ALTER TYPE case_status_enum ADD VALUE IF NOT EXISTS 'CLOSED'")


def downgrade() -> None:
    pass
