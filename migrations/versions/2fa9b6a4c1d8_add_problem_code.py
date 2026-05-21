"""add problem code

Revision ID: 2fa9b6a4c1d8
Revises: 7b8d1f2e9c43
Create Date: 2026-05-21 07:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2fa9b6a4c1d8'
down_revision = '7b8d1f2e9c43'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('problem', schema=None) as batch_op:
        batch_op.add_column(sa.Column('problem_code', sa.String(length=40), nullable=True))

    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT id FROM problem ORDER BY id ASC")).fetchall()
    for row in rows:
        connection.execute(
            sa.text("UPDATE problem SET problem_code = :problem_code WHERE id = :problem_id"),
            {"problem_code": f"P{999 + row.id}", "problem_id": row.id},
        )

    with op.batch_alter_table('problem', schema=None) as batch_op:
        batch_op.alter_column('problem_code', existing_type=sa.String(length=40), nullable=False)
        batch_op.create_index(batch_op.f('ix_problem_problem_code'), ['problem_code'], unique=True)


def downgrade():
    with op.batch_alter_table('problem', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_problem_problem_code'))
        batch_op.drop_column('problem_code')
