"""add ast rules for oj

Revision ID: 5c6fd53c2ab1
Revises: 2fa9b6a4c1d8
Create Date: 2026-05-23 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

from utils.ast_checker import get_default_ast_rule_templates


# revision identifiers, used by Alembic.
revision = '5c6fd53c2ab1'
down_revision = '2fa9b6a4c1d8'
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


def _insert_missing_default_templates(connection):
    templates_table = sa.table(
        'ast_rule_templates',
        sa.column('code', sa.String(length=80)),
        sa.column('name', sa.String(length=200)),
        sa.column('category', sa.String(length=80)),
        sa.column('rule_type', sa.String(length=80)),
        sa.column('target', sa.String(length=120)),
        sa.column('description', sa.Text()),
        sa.column('default_params', sa.JSON()),
        sa.column('enabled', sa.Boolean()),
        sa.column('sort_order', sa.Integer()),
    )
    existing_codes = {
        row[0]
        for row in connection.execute(sa.text("SELECT code FROM ast_rule_templates")).fetchall()
    }
    missing_templates = [
        template
        for template in get_default_ast_rule_templates()
        if template["code"] not in existing_codes
    ]
    if missing_templates:
        connection.execute(templates_table.insert(), missing_templates)


def upgrade():
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if not _column_exists(inspector, 'problem', 'ast_check_enabled'):
        with op.batch_alter_table('problem', schema=None) as batch_op:
            batch_op.add_column(sa.Column('ast_check_enabled', sa.Boolean(), nullable=False, server_default=sa.false()))
        inspector = sa.inspect(connection)

    if not _table_exists(inspector, 'ast_rule_templates'):
        op.create_table(
            'ast_rule_templates',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('code', sa.String(length=80), nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('category', sa.String(length=80), nullable=False),
            sa.Column('rule_type', sa.String(length=80), nullable=False),
            sa.Column('target', sa.String(length=120), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('default_params', sa.JSON(), nullable=False),
            sa.Column('enabled', sa.Boolean(), nullable=False),
            sa.Column('sort_order', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_ast_rule_templates')),
            sa.UniqueConstraint('code', name=op.f('uq_ast_rule_templates_code')),
        )
        inspector = sa.inspect(connection)
    if not _index_exists(inspector, 'ast_rule_templates', op.f('ix_ast_rule_templates_code')):
        with op.batch_alter_table('ast_rule_templates', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_ast_rule_templates_code'), ['code'], unique=True)
        inspector = sa.inspect(connection)

    if not _table_exists(inspector, 'problem_ast_rules'):
        op.create_table(
            'problem_ast_rules',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('problem_id', sa.Integer(), nullable=False),
            sa.Column('template_id', sa.Integer(), nullable=True),
            sa.Column('rule_type', sa.String(length=80), nullable=False),
            sa.Column('target', sa.String(length=120), nullable=False),
            sa.Column('min_count', sa.Integer(), nullable=True),
            sa.Column('max_count', sa.Integer(), nullable=True),
            sa.Column('required_value', sa.String(length=255), nullable=True),
            sa.Column('params', sa.JSON(), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('fail_message', sa.Text(), nullable=False),
            sa.Column('enabled', sa.Boolean(), nullable=False),
            sa.Column('sort_order', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['problem_id'], ['problem.id'], name=op.f('fk_problem_ast_rules_problem_id_problem')),
            sa.ForeignKeyConstraint(['template_id'], ['ast_rule_templates.id'], name=op.f('fk_problem_ast_rules_template_id_ast_rule_templates')),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_problem_ast_rules')),
        )
        inspector = sa.inspect(connection)
    with op.batch_alter_table('problem_ast_rules', schema=None) as batch_op:
        if not _index_exists(inspector, 'problem_ast_rules', op.f('ix_problem_ast_rules_problem_id')):
            batch_op.create_index(batch_op.f('ix_problem_ast_rules_problem_id'), ['problem_id'], unique=False)
        if not _index_exists(inspector, 'problem_ast_rules', op.f('ix_problem_ast_rules_template_id')):
            batch_op.create_index(batch_op.f('ix_problem_ast_rules_template_id'), ['template_id'], unique=False)

    _insert_missing_default_templates(connection)

    if _column_exists(inspector, 'problem', 'ast_check_enabled'):
        with op.batch_alter_table('problem', schema=None) as batch_op:
            batch_op.alter_column('ast_check_enabled', server_default=None)


def downgrade():
    with op.batch_alter_table('problem_ast_rules', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_problem_ast_rules_template_id'))
        batch_op.drop_index(batch_op.f('ix_problem_ast_rules_problem_id'))
    op.drop_table('problem_ast_rules')

    with op.batch_alter_table('ast_rule_templates', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_ast_rule_templates_code'))
    op.drop_table('ast_rule_templates')

    with op.batch_alter_table('problem', schema=None) as batch_op:
        batch_op.drop_column('ast_check_enabled')
