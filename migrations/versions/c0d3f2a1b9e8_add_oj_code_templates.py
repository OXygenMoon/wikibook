"""add oj code templates

Revision ID: c0d3f2a1b9e8
Revises: a4d8f1c3e2b7
Create Date: 2026-05-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'c0d3f2a1b9e8'
down_revision = 'a4d8f1c3e2b7'
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

    if _table_exists(inspector, 'problem') and not _column_exists(inspector, 'problem', 'python_template'):
        with op.batch_alter_table('problem', schema=None) as batch_op:
            batch_op.add_column(sa.Column('python_template', sa.Text(), nullable=True))
        inspector = sa.inspect(connection)

    if not _table_exists(inspector, 'oj_user_setting'):
        op.create_table(
            'oj_user_setting',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('python_template', sa.Text(), nullable=True),
            sa.Column('default_language', sa.String(length=32), nullable=False, server_default='python'),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk_oj_user_setting_user_id_user')),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_oj_user_setting')),
            sa.UniqueConstraint('user_id', name=op.f('uq_oj_user_setting_user_id')),
        )
        inspector = sa.inspect(connection)

    if _table_exists(inspector, 'oj_user_setting') and not _index_exists(inspector, 'oj_user_setting', op.f('ix_oj_user_setting_user_id')):
        with op.batch_alter_table('oj_user_setting', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_oj_user_setting_user_id'), ['user_id'], unique=True)

    if _column_exists(inspector, 'oj_user_setting', 'default_language'):
        with op.batch_alter_table('oj_user_setting', schema=None) as batch_op:
            batch_op.alter_column('default_language', server_default=None)


def downgrade():
    inspector = sa.inspect(op.get_bind())

    if _table_exists(inspector, 'oj_user_setting'):
        with op.batch_alter_table('oj_user_setting', schema=None) as batch_op:
            if _index_exists(inspector, 'oj_user_setting', op.f('ix_oj_user_setting_user_id')):
                batch_op.drop_index(batch_op.f('ix_oj_user_setting_user_id'))
        op.drop_table('oj_user_setting')

    if _column_exists(inspector, 'problem', 'python_template'):
        with op.batch_alter_table('problem', schema=None) as batch_op:
            batch_op.drop_column('python_template')
