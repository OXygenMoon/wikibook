"""add oj list query indexes

Revision ID: a4d8f1c3e2b7
Revises: 8a3f0d2c6b91
Create Date: 2026-05-24 00:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'a4d8f1c3e2b7'
down_revision = '8a3f0d2c6b91'
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
    with op.batch_alter_table('judge_task', schema=None) as batch_op:
        _create_index_if_missing(batch_op, connection, 'judge_task', batch_op.f('ix_judge_task_assignment_created_id'), ['assignment_id', 'created_at', 'id'])
        _create_index_if_missing(batch_op, connection, 'judge_task', batch_op.f('ix_judge_task_problem_assignment_created_id'), ['problem_id', 'assignment_id', 'created_at', 'id'])
        _create_index_if_missing(batch_op, connection, 'judge_task', batch_op.f('ix_judge_task_user_assignment_created_id'), ['user_id', 'assignment_id', 'created_at', 'id'])

    with op.batch_alter_table('judge_task_result', schema=None) as batch_op:
        _create_index_if_missing(batch_op, connection, 'judge_task_result', batch_op.f('ix_judge_task_result_task_case_status'), ['task_id', 'case_index', 'status'])

    with op.batch_alter_table('problem', schema=None) as batch_op:
        _create_index_if_missing(batch_op, connection, 'problem', batch_op.f('ix_problem_visible_difficulty_code_id'), ['is_visible', 'difficulty', 'problem_code', 'id'])

    with op.batch_alter_table('problem_test_case', schema=None) as batch_op:
        _create_index_if_missing(batch_op, connection, 'problem_test_case', batch_op.f('ix_problem_test_case_problem_sort'), ['problem_id', 'sort_order'])

    with op.batch_alter_table('problem_file', schema=None) as batch_op:
        _create_index_if_missing(batch_op, connection, 'problem_file', batch_op.f('ix_problem_file_problem_filename'), ['problem_id', 'filename'])


def downgrade():
    with op.batch_alter_table('problem_file', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_problem_file_problem_filename'))

    with op.batch_alter_table('problem_test_case', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_problem_test_case_problem_sort'))

    with op.batch_alter_table('problem', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_problem_visible_difficulty_code_id'))

    with op.batch_alter_table('judge_task_result', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_judge_task_result_task_case_status'))

    with op.batch_alter_table('judge_task', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_judge_task_user_assignment_created_id'))
        batch_op.drop_index(batch_op.f('ix_judge_task_problem_assignment_created_id'))
        batch_op.drop_index(batch_op.f('ix_judge_task_assignment_created_id'))
