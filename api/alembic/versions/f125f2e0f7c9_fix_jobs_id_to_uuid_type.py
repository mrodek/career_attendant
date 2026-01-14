"""fix_jobs_id_to_uuid_type

Revision ID: f125f2e0f7c9
Revises: fix_jobs_id_uuid
Create Date: 2026-01-14 10:49:49.197425

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f125f2e0f7c9'
down_revision: Union[str, None] = '29cfa1f992ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert jobs.id from VARCHAR to UUID
    # The USING clause tells PostgreSQL how to convert the existing VARCHAR values to UUID
    op.execute('ALTER TABLE jobs ALTER COLUMN id TYPE UUID USING id::uuid')
    
    # Convert saved_jobs.job_id from VARCHAR to UUID (foreign key)
    op.execute('ALTER TABLE saved_jobs ALTER COLUMN job_id TYPE UUID USING job_id::uuid')


def downgrade() -> None:
    # Convert back to VARCHAR if needed
    op.execute('ALTER TABLE jobs ALTER COLUMN id TYPE VARCHAR USING id::text')
    op.execute('ALTER TABLE saved_jobs ALTER COLUMN job_id TYPE VARCHAR USING job_id::text')
