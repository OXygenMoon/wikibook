"""add oj problem tables

Revision ID: c1c41f1d8a31
Revises: 9e62f14f4f5d
Create Date: 2026-05-20 16:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c1c41f1d8a31'
down_revision = '9e62f14f4f5d'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'problem',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('slug', sa.String(length=200), nullable=False),
        sa.Column('statement_md', sa.Text(), nullable=False),
        sa.Column('input_spec_md', sa.Text(), nullable=False),
        sa.Column('output_spec_md', sa.Text(), nullable=False),
        sa.Column('hint_md', sa.Text(), nullable=False),
        sa.Column('source', sa.String(length=200), nullable=True),
        sa.Column('difficulty', sa.String(length=20), nullable=False),
        sa.Column('time_limit_ms', sa.Integer(), nullable=False),
        sa.Column('memory_limit_mb', sa.Integer(), nullable=False),
        sa.Column('allowed_languages', sa.JSON(), nullable=False),
        sa.Column('is_visible', sa.Boolean(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], name=op.f('fk_problem_created_by_id_user')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_problem')),
        sa.UniqueConstraint('slug', name=op.f('uq_problem_slug')),
    )

    op.create_table(
        'problem_test_case',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('problem_id', sa.Integer(), nullable=False),
        sa.Column('case_type', sa.String(length=20), nullable=False),
        sa.Column('input_data', sa.Text(), nullable=False),
        sa.Column('expected_output', sa.Text(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['problem_id'], ['problem.id'], name=op.f('fk_problem_test_case_problem_id_problem')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_problem_test_case')),
    )


def downgrade():
    op.drop_table('problem_test_case')
    op.drop_table('problem')
