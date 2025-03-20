"""update character

Revision ID: 5502aa343b5c
Revises: 2d024cf145a1
Create Date: 2025-03-20 11:21:28.586849

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision = "5502aa343b5c"
down_revision = "2d024cf145a1"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "chuni_static_character",
        sa.Column("illustrator", mysql.VARCHAR(length=255), nullable=True),
    )
    op.add_column(
        "chuni_static_character",
        sa.Column("addImages", sa.JSON(), nullable=True),
    )


def downgrade():
    op.drop_column("chuni_static_character", "illustrator")
    op.drop_column("chuni_static_character", "addImages")
