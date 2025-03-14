"""mai2_favorite_song_ordering

Revision ID: bc91c1206dca
Revises: 28443e2da5b8
Create Date: 2024-09-16 14:24:56.714066

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bc91c1206dca'
down_revision = '28443e2da5b8'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('mai2_item_favorite_music', sa.Column('orderId', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('mai2_item_favorite_music', 'orderId')
