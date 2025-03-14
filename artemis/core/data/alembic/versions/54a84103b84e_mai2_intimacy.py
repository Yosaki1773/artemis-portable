"""mai2_intimacy

Revision ID: 54a84103b84e
Revises: bc91c1206dca
Create Date: 2024-09-16 17:47:49.164546

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Column, Integer, UniqueConstraint

# revision identifiers, used by Alembic.
revision = '54a84103b84e'
down_revision = 'bc91c1206dca'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "mai2_user_intimate",
        Column("id", Integer, primary_key=True, nullable=False),
        Column("user", Integer, nullable=False),
        Column("partnerId", Integer, nullable=False),
        Column("intimateLevel", Integer, nullable=False),
        Column("intimateCountRewarded", Integer, nullable=False),
        UniqueConstraint("user", "partnerId", name="mai2_user_intimate_uk"),
        mysql_charset="utf8mb4",
    )

    op.create_foreign_key(
        None,
        "mai2_user_intimate",
        "aime_user",
        ["user"],
        ["id"],
        ondelete="cascade",
        onupdate="cascade",
    )


def downgrade():
    op.drop_table("mai2_user_intimate")
