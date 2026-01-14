"""Add llm_extracted_comprehensive to Job model

Revision ID: 29cfa1f992ef
Revises: 765a7fd2a9bf
Create Date: 2026-01-13 22:42:06.340444

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '29cfa1f992ef'
down_revision: Union[str, None] = '765a7fd2a9bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('jobs', sa.Column('llm_extracted_comprehensive', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('jobs', 'llm_extracted_comprehensive')
