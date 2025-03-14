"""mai2_buddies_plus

Revision ID: 28443e2da5b8
Revises: 5ea73f89d982
Create Date: 2024-09-15 20:44:02.351819

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '28443e2da5b8'
down_revision = '5ea73f89d982'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('mai2_profile_detail', sa.Column('point', sa.Integer()))
    op.add_column('mai2_profile_detail', sa.Column('totalPoint', sa.Integer()))
    op.add_column('mai2_profile_detail', sa.Column('friendRegistSkip', sa.SmallInteger()))


def downgrade():
    op.drop_column('mai2_profile_detail', 'point')
    op.drop_column('mai2_profile_detail', 'totalPoint')
    op.drop_column('mai2_profile_detail', 'friendRegistSkip')
