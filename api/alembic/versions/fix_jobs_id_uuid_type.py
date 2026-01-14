"""fix jobs.id to UUID type

Revision ID: fix_jobs_id_uuid
Revises: 29cfa1f992ef
Create Date: 2026-01-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fix_jobs_id_uuid'
down_revision = '29cfa1f992ef'
branch_labels = None
depends_on = None


def upgrade():
    # Convert jobs.id from VARCHAR to UUID
    # The USING clause tells PostgreSQL how to convert the existing VARCHAR values to UUID
    op.execute('ALTER TABLE jobs ALTER COLUMN id TYPE UUID USING id::uuid')
    
    # Convert saved_jobs.job_id from VARCHAR to UUID (foreign key)
    op.execute('ALTER TABLE saved_jobs ALTER COLUMN job_id TYPE UUID USING job_id::uuid')


def downgrade():
    # Convert back to VARCHAR if needed
    op.execute('ALTER TABLE jobs ALTER COLUMN id TYPE VARCHAR USING id::text')
    op.execute('ALTER TABLE saved_jobs ALTER COLUMN job_id TYPE VARCHAR USING job_id::text')
