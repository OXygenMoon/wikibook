"""merge heads and add judge tables

Revision ID: 9e62f14f4f5d
Revises: b2508e5693ab, c4f7a8b21d1e
Create Date: 2026-05-20 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9e62f14f4f5d'
down_revision = ('b2508e5693ab', 'c4f7a8b21d1e')
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'judge_task',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('submission_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('language', sa.String(length=32), nullable=False),
        sa.Column('source_code', sa.Text(), nullable=False),
        sa.Column('test_cases', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('queue_job_id', sa.String(length=64), nullable=True),
        sa.Column('runtime_image', sa.String(length=255), nullable=True),
        sa.Column('time_limit_ms', sa.Integer(), nullable=False),
        sa.Column('memory_limit_mb', sa.Integer(), nullable=False),
        sa.Column('total_score', sa.Integer(), nullable=False),
        sa.Column('passed_count', sa.Integer(), nullable=False),
        sa.Column('total_count', sa.Integer(), nullable=False),
        sa.Column('result_summary', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['submission_id'], ['submission.id'], name=op.f('fk_judge_task_submission_id_submission')),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk_judge_task_user_id_user')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_judge_task')),
    )
    with op.batch_alter_table('judge_task', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_judge_task_queue_job_id'), ['queue_job_id'], unique=False)

    op.create_table(
        'judge_task_result',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('case_index', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('time_ms', sa.Integer(), nullable=False),
        sa.Column('memory_kb', sa.Integer(), nullable=False),
        sa.Column('input_data', sa.Text(), nullable=True),
        sa.Column('expected_output', sa.Text(), nullable=True),
        sa.Column('actual_output', sa.Text(), nullable=True),
        sa.Column('stderr_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['judge_task.id'], name=op.f('fk_judge_task_result_task_id_judge_task')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_judge_task_result')),
    )


def downgrade():
    op.drop_table('judge_task_result')
    with op.batch_alter_table('judge_task', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_judge_task_queue_job_id'))
    op.drop_table('judge_task')
