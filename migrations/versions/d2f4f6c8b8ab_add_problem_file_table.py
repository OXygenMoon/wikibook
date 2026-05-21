"""add problem file table

Revision ID: d2f4f6c8b8ab
Revises: c1c41f1d8a31
Create Date: 2026-05-20 21:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd2f4f6c8b8ab'
down_revision = 'c1c41f1d8a31'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'problem_file',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('problem_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('stored_filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('content_type', sa.String(length=120), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('uploaded_by_id', sa.Integer(), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['problem_id'], ['problem.id'], name=op.f('fk_problem_file_problem_id_problem')),
        sa.ForeignKeyConstraint(['uploaded_by_id'], ['user.id'], name=op.f('fk_problem_file_uploaded_by_id_user')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_problem_file')),
    )


def downgrade():
    op.drop_table('problem_file')
