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
    # Step 1: Drop the foreign key constraint
    op.execute('ALTER TABLE saved_jobs DROP CONSTRAINT IF EXISTS fk_saved_jobs_job_id')
    op.execute('ALTER TABLE saved_jobs DROP CONSTRAINT IF EXISTS saved_jobs_job_id_fkey')
    
    # Step 2: Convert both columns to UUID
    op.execute('ALTER TABLE jobs ALTER COLUMN id TYPE UUID USING id::uuid')
    op.execute('ALTER TABLE saved_jobs ALTER COLUMN job_id TYPE UUID USING job_id::uuid')
    
    # Step 3: Recreate the foreign key constraint
    op.execute('ALTER TABLE saved_jobs ADD CONSTRAINT saved_jobs_job_id_fkey FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE')


def downgrade() -> None:
    # Convert back to VARCHAR if needed
    op.execute('ALTER TABLE jobs ALTER COLUMN id TYPE VARCHAR USING id::text')
    op.execute('ALTER TABLE saved_jobs ALTER COLUMN job_id TYPE VARCHAR USING job_id::text')
