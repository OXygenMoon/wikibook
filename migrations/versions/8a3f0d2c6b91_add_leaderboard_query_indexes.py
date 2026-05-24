"""add leaderboard query indexes

Revision ID: 8a3f0d2c6b91
Revises: 5c6fd53c2ab1
Create Date: 2026-05-24 00:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '8a3f0d2c6b91'
down_revision = '5c6fd53c2ab1'
branch_labels = None
depends_on = None


def _index_exists(connection, table_name, index_name):
    return index_name in {
        index["name"]
        for index in op.get_context().impl.dialect.get_indexes(connection, table_name)
    }


def _create_index_if_missing(batch_op, connection, table_name, index_name, columns):
    if not _index_exists(connection, table_name, index_name):
        batch_op.create_index(index_name, columns, unique=False)


def upgrade():
    connection = op.get_bind()
    with op.batch_alter_table('study_session', schema=None) as batch_op:
        _create_index_if_missing(batch_op, connection, 'study_session', batch_op.f('ix_study_session_user_start_time'), ['user_id', 'start_time'])

    with op.batch_alter_table('note', schema=None) as batch_op:
        _create_index_if_missing(batch_op, connection, 'note', batch_op.f('ix_note_user_created_at'), ['user_id', 'created_at'])

    with op.batch_alter_table('wiki_page_history', schema=None) as batch_op:
        _create_index_if_missing(batch_op, connection, 'wiki_page_history', batch_op.f('ix_wiki_page_history_user_created_at'), ['user_id', 'created_at'])

    with op.batch_alter_table('pomodoro_record', schema=None) as batch_op:
        _create_index_if_missing(batch_op, connection, 'pomodoro_record', batch_op.f('ix_pomodoro_record_user_completed_at'), ['user_id', 'completed_at'])

    with op.batch_alter_table('judge_task', schema=None) as batch_op:
        _create_index_if_missing(batch_op, connection, 'judge_task', batch_op.f('ix_judge_task_user_created_at'), ['user_id', 'created_at'])
        _create_index_if_missing(batch_op, connection, 'judge_task', batch_op.f('ix_judge_task_user_status_problem'), ['user_id', 'status', 'problem_id'])


def downgrade():
    with op.batch_alter_table('judge_task', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_judge_task_user_status_problem'))
        batch_op.drop_index(batch_op.f('ix_judge_task_user_created_at'))

    with op.batch_alter_table('pomodoro_record', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_pomodoro_record_user_completed_at'))

    with op.batch_alter_table('wiki_page_history', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_wiki_page_history_user_created_at'))

    with op.batch_alter_table('note', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_note_user_created_at'))

    with op.batch_alter_table('study_session', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_study_session_user_start_time'))
