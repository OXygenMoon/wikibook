"""add problem id to judge task

Revision ID: 7b8d1f2e9c43
Revises: d2f4f6c8b8ab
Create Date: 2026-05-20 22:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7b8d1f2e9c43'
down_revision = 'd2f4f6c8b8ab'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('judge_task', schema=None) as batch_op:
        batch_op.add_column(sa.Column('problem_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            batch_op.f('fk_judge_task_problem_id_problem'),
            'problem',
            ['problem_id'],
            ['id'],
        )
        batch_op.create_index(batch_op.f('ix_judge_task_problem_id'), ['problem_id'], unique=False)


def downgrade():
    with op.batch_alter_table('judge_task', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_judge_task_problem_id'))
        batch_op.drop_constraint(batch_op.f('fk_judge_task_problem_id_problem'), type_='foreignkey')
        batch_op.drop_column('problem_id')
