"""add oj training graph tables

Revision ID: e8b7d3f4a901
Revises: c0d3f2a1b9e8
Create Date: 2026-05-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'e8b7d3f4a901'
down_revision = 'c0d3f2a1b9e8'
branch_labels = None
depends_on = None


def _table_exists(inspector, table_name):
    return table_name in inspector.get_table_names()


def _index_exists(inspector, table_name, index_name):
    if not _table_exists(inspector, table_name):
        return False
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade():
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if not _table_exists(inspector, 'oj_training_project'):
        op.create_table(
            'oj_training_project',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=200), nullable=False),
            sa.Column('description_md', sa.Text(), nullable=True),
            sa.Column('visibility', sa.String(length=20), nullable=False, server_default='all'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('created_by_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], name=op.f('fk_oj_training_project_created_by_id_user')),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_oj_training_project')),
        )
        inspector = sa.inspect(connection)

    if not _table_exists(inspector, 'oj_training_chapter'):
        op.create_table(
            'oj_training_chapter',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('project_id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=200), nullable=False),
            sa.Column('description_md', sa.Text(), nullable=True),
            sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('canvas_width', sa.Integer(), nullable=False, server_default='1400'),
            sa.Column('canvas_height', sa.Integer(), nullable=False, server_default='820'),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['project_id'], ['oj_training_project.id'], name=op.f('fk_oj_training_chapter_project_id_oj_training_project')),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_oj_training_chapter')),
        )
        inspector = sa.inspect(connection)

    if not _table_exists(inspector, 'oj_training_node'):
        op.create_table(
            'oj_training_node',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('chapter_id', sa.Integer(), nullable=False),
            sa.Column('problem_id', sa.Integer(), nullable=False),
            sa.Column('label', sa.String(length=200), nullable=True),
            sa.Column('note', sa.Text(), nullable=True),
            sa.Column('pos_x', sa.Integer(), nullable=False, server_default='120'),
            sa.Column('pos_y', sa.Integer(), nullable=False, server_default='120'),
            sa.Column('width', sa.Integer(), nullable=False, server_default='220'),
            sa.Column('height', sa.Integer(), nullable=False, server_default='120'),
            sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('is_entry', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('is_core', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['chapter_id'], ['oj_training_chapter.id'], name=op.f('fk_oj_training_node_chapter_id_oj_training_chapter')),
            sa.ForeignKeyConstraint(['problem_id'], ['problem.id'], name=op.f('fk_oj_training_node_problem_id_problem')),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_oj_training_node')),
        )
        inspector = sa.inspect(connection)

    if not _table_exists(inspector, 'oj_training_edge'):
        op.create_table(
            'oj_training_edge',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('from_node_id', sa.Integer(), nullable=False),
            sa.Column('to_node_id', sa.Integer(), nullable=False),
            sa.Column('label', sa.String(length=120), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['from_node_id'], ['oj_training_node.id'], name=op.f('fk_oj_training_edge_from_node_id_oj_training_node')),
            sa.ForeignKeyConstraint(['to_node_id'], ['oj_training_node.id'], name=op.f('fk_oj_training_edge_to_node_id_oj_training_node')),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_oj_training_edge')),
            sa.UniqueConstraint('from_node_id', 'to_node_id', name=op.f('uq_oj_training_edge_from_to')),
        )
        inspector = sa.inspect(connection)

    association_tables = [
        ('oj_training_classes', 'class_id', 'class'),
        ('oj_training_groups', 'group_id', 'group'),
        ('oj_training_users', 'user_id', 'user'),
        ('oj_training_managers', 'user_id', 'user'),
    ]
    for table_name, target_column, target_table in association_tables:
        if not _table_exists(inspector, table_name):
            op.create_table(
                table_name,
                sa.Column('training_id', sa.Integer(), nullable=False),
                sa.Column(target_column, sa.Integer(), nullable=False),
                sa.ForeignKeyConstraint(['training_id'], ['oj_training_project.id'], name=op.f(f'fk_{table_name}_training_id_oj_training_project')),
                sa.ForeignKeyConstraint([target_column], [f'{target_table}.id'], name=op.f(f'fk_{table_name}_{target_column}_{target_table}')),
                sa.PrimaryKeyConstraint('training_id', target_column, name=op.f(f'pk_{table_name}')),
            )
            inspector = sa.inspect(connection)

    index_specs = [
        ('oj_training_chapter', op.f('ix_oj_training_chapter_project_id'), ['project_id']),
        ('oj_training_node', op.f('ix_oj_training_node_chapter_id'), ['chapter_id']),
        ('oj_training_node', op.f('ix_oj_training_node_problem_id'), ['problem_id']),
        ('oj_training_edge', op.f('ix_oj_training_edge_from_node_id'), ['from_node_id']),
        ('oj_training_edge', op.f('ix_oj_training_edge_to_node_id'), ['to_node_id']),
    ]
    for table_name, index_name, columns in index_specs:
        if _table_exists(inspector, table_name) and not _index_exists(inspector, table_name, index_name):
            with op.batch_alter_table(table_name, schema=None) as batch_op:
                batch_op.create_index(index_name, columns, unique=False)


def downgrade():
    inspector = sa.inspect(op.get_bind())
    for table_name in (
        'oj_training_managers',
        'oj_training_users',
        'oj_training_groups',
        'oj_training_classes',
        'oj_training_edge',
        'oj_training_node',
        'oj_training_chapter',
        'oj_training_project',
    ):
        if _table_exists(inspector, table_name):
            op.drop_table(table_name)
            inspector = sa.inspect(op.get_bind())
