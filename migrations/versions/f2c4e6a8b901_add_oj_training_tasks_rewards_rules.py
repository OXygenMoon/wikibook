"""add oj training tasks rewards rules

Revision ID: f2c4e6a8b901
Revises: e8b7d3f4a901
Create Date: 2026-05-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'f2c4e6a8b901'
down_revision = 'e8b7d3f4a901'
branch_labels = None
depends_on = None


def _table_exists(inspector, table_name):
    return table_name in inspector.get_table_names()


def _column_exists(inspector, table_name, column_name):
    if not _table_exists(inspector, table_name):
        return False
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _index_exists(inspector, table_name, index_name):
    if not _table_exists(inspector, table_name):
        return False
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade():
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if _table_exists(inspector, 'oj_training_edge'):
        with op.batch_alter_table('oj_training_edge', schema=None) as batch_op:
            if not _column_exists(inspector, 'oj_training_edge', 'requirement_type'):
                batch_op.add_column(sa.Column('requirement_type', sa.String(length=40), nullable=False, server_default='all_completed'))
            if not _column_exists(inspector, 'oj_training_edge', 'min_completed'):
                batch_op.add_column(sa.Column('min_completed', sa.Integer(), nullable=False, server_default='1'))
            if not _column_exists(inspector, 'oj_training_edge', 'is_hidden'):
                batch_op.add_column(sa.Column('is_hidden', sa.Boolean(), nullable=False, server_default=sa.false()))
        inspector = sa.inspect(connection)

    if not _table_exists(inspector, 'oj_training_task'):
        op.create_table(
            'oj_training_task',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('node_id', sa.Integer(), nullable=False),
            sa.Column('task_type', sa.String(length=40), nullable=False, server_default='oj_problem_ac'),
            sa.Column('problem_id', sa.Integer(), nullable=True),
            sa.Column('title', sa.String(length=200), nullable=False, server_default=''),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('target_value', sa.String(length=200), nullable=True),
            sa.Column('required_count', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('is_required', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['node_id'], ['oj_training_node.id'], name=op.f('fk_oj_training_task_node_id_oj_training_node')),
            sa.ForeignKeyConstraint(['problem_id'], ['problem.id'], name=op.f('fk_oj_training_task_problem_id_problem')),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_oj_training_task')),
        )
        inspector = sa.inspect(connection)

    if not _table_exists(inspector, 'oj_training_reward'):
        op.create_table(
            'oj_training_reward',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('node_id', sa.Integer(), nullable=False),
            sa.Column('reward_type', sa.String(length=40), nullable=False, server_default='unlock'),
            sa.Column('title', sa.String(length=200), nullable=False, server_default=''),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('value', sa.String(length=200), nullable=True),
            sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('is_auto_claim', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['node_id'], ['oj_training_node.id'], name=op.f('fk_oj_training_reward_node_id_oj_training_node')),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_oj_training_reward')),
        )
        inspector = sa.inspect(connection)

    index_specs = [
        ('oj_training_task', op.f('ix_oj_training_task_node_id'), ['node_id']),
        ('oj_training_task', op.f('ix_oj_training_task_problem_id'), ['problem_id']),
        ('oj_training_reward', op.f('ix_oj_training_reward_node_id'), ['node_id']),
    ]
    for table_name, index_name, columns in index_specs:
        if _table_exists(inspector, table_name) and not _index_exists(inspector, table_name, index_name):
            with op.batch_alter_table(table_name, schema=None) as batch_op:
                batch_op.create_index(index_name, columns, unique=False)

    if _table_exists(inspector, 'oj_training_task'):
        connection.execute(sa.text(
            """
            INSERT INTO oj_training_task (
                node_id, task_type, problem_id, title, description,
                target_value, required_count, is_required, sort_order, created_at, updated_at
            )
            SELECT n.id, 'oj_problem_ac', n.problem_id, COALESCE(NULLIF(n.label, ''), p.title),
                   '完成关联 OJ 题目', 'accepted', 1, 1, 0, n.created_at, n.updated_at
            FROM oj_training_node AS n
            JOIN problem AS p ON p.id = n.problem_id
            WHERE NOT EXISTS (
                SELECT 1 FROM oj_training_task AS t WHERE t.node_id = n.id
            )
            """
        ))


def downgrade():
    inspector = sa.inspect(op.get_bind())
    if _table_exists(inspector, 'oj_training_reward'):
        op.drop_table('oj_training_reward')
    inspector = sa.inspect(op.get_bind())
    if _table_exists(inspector, 'oj_training_task'):
        op.drop_table('oj_training_task')
    inspector = sa.inspect(op.get_bind())
    if _table_exists(inspector, 'oj_training_edge'):
        with op.batch_alter_table('oj_training_edge', schema=None) as batch_op:
            if _column_exists(inspector, 'oj_training_edge', 'is_hidden'):
                batch_op.drop_column('is_hidden')
            if _column_exists(inspector, 'oj_training_edge', 'min_completed'):
                batch_op.drop_column('min_completed')
            if _column_exists(inspector, 'oj_training_edge', 'requirement_type'):
                batch_op.drop_column('requirement_type')
