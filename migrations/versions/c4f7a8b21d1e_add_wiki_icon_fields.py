"""add wiki icon fields

Revision ID: c4f7a8b21d1e
Revises: 7af4a352f656
Create Date: 2026-05-19 15:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c4f7a8b21d1e'
down_revision = '7af4a352f656'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('wiki', schema=None) as batch_op:
        batch_op.add_column(sa.Column('icon_url', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('icon_scale', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('icon_position_x', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('icon_position_y', sa.Float(), nullable=True))


def downgrade():
    with op.batch_alter_table('wiki', schema=None) as batch_op:
        batch_op.drop_column('icon_position_y')
        batch_op.drop_column('icon_position_x')
        batch_op.drop_column('icon_scale')
        batch_op.drop_column('icon_url')
